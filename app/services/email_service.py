import logging
import traceback
from flask_mail import Message
from flask import current_app
from datetime import datetime

from app import mail, db
from app.models import ConsumoPOS

logger = logging.getLogger(__name__)

# Valores que indican claramente que la credencial es un placeholder sin configurar.
_PLACEHOLDER_PASSWORDS = {
    '', 'CHANGE_ME_APP_PASSWORD', 'tu-contraseña-de-aplicacion-aqui',
    'tu-contrasena-de-aplicacion-aqui', 'changeme', 'password', 'test',
}


class EmailService:
    @staticmethod
    def _smtp_configurado():
        """True si hay credenciales SMTP reales (no placeholders)."""
        cfg = current_app.config
        user = (cfg.get('MAIL_USERNAME') or '').strip()
        pwd = (cfg.get('MAIL_PASSWORD') or '').strip()
        if not user or not pwd:
            return False, 'MAIL_USERNAME/MAIL_PASSWORD no configurados'
        if pwd in _PLACEHOLDER_PASSWORDS:
            return False, 'MAIL_PASSWORD es un valor placeholder (no es una App Password real)'
        return True, ''

    @staticmethod
    def enviar_correo(subject, recipients, html_body):
        """Envío base con logging real. Nunca lanza: devuelve True/False.

        En tests (MAIL_SUPPRESS_SEND=True o TESTING) no se envía de verdad:
        se registra en el log y se devuelve True para no romper flujos.
        """
        try:
            if current_app.config.get('MAIL_SUPPRESS_SEND') or current_app.config.get('TESTING'):
                logger.info("MAIL_SUPPRESS_SEND activo: correo simulado a %s | asunto=%s", recipients, subject)
                return True

            ok, motivo = EmailService._smtp_configurado()
            if not ok:
                logger.warning("Correo NO enviado a %s: %s", recipients, motivo)
                return False

            sender = current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME')
            msg = Message(subject=subject, sender=sender, recipients=recipients, html=html_body)
            mail.send(msg)
            logger.info("Correo enviado a %s | asunto=%s", recipients, subject)
            return True
        except Exception as e:
            logger.error("Error enviando correo a %s | asunto=%s: %s\n%s",
                         recipients, subject, e, traceback.format_exc())
            return False

    @staticmethod
    def _marcar_email(reserva, enviado, error=None):
        """Persiste el estado del correo SIN tocar el resto de la reserva.

        Se usa en un commit separado para que un fallo de correo jamás
        deje la reserva en estado inconsistente.
        """
        try:
            reserva.email_intentos = (reserva.email_intentos or 0) + 1
            if enviado:
                reserva.email_estado = 'enviado'
                reserva.email_error = None
                reserva.email_enviado_en = datetime.now()
            else:
                reserva.email_estado = 'fallido'
                reserva.email_error = (error or 'Fallo desconocido')[:1000]
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("No se pudo persistir email_estado de reserva %s: %s",
                         getattr(reserva, 'id', '?'), e)

    @staticmethod
    def enviar_confirmacion_reserva(reserva, habitacion, config):
        """Envía el correo de confirmación y registra el resultado en la reserva.

        La reserva YA debe estar commiteada antes de llamar aquí. Este método
        hace su propio commit solo para los campos email_*.
        Devuelve True si el correo salió, False en caso contrario.
        """
        if not reserva.email_cliente:
            try:
                reserva.email_estado = 'no_aplica'
                reserva.email_error = 'Reserva sin email_cliente'
                db.session.commit()
            except Exception:
                db.session.rollback()
            logger.warning("Reserva %s sin email: confirmación no enviada.", getattr(reserva, 'codigo', '?'))
            return False

        ok = EmailService.enviar_codigo_reserva(reserva, habitacion, config)
        if ok:
            EmailService._marcar_email(reserva, True)
        else:
            _, motivo = EmailService._smtp_configurado()
            EmailService._marcar_email(reserva, False, error=motivo or 'Fallo de envío SMTP (ver logs)')
        return ok

    @staticmethod
    def enviar_factura(factura, reserva, habitacion, config):
        if not reserva.email_cliente:
            return False
        
        noches = (reserva.fecha_fin - reserva.fecha_inicio).days
        
        consumos = db.session.query(ConsumoPOS).filter_by(reservacion_id=reserva.id).all()
        total_extras = sum(c.monto for c in consumos)
        costo_alojamiento = factura.total - total_extras
        
        # Build consumption rows with better styling
        rows_consumos = ""
        for i, c in enumerate(consumos):
            bg_color = "#fdfafa" if i % 2 == 0 else "#ffffff"
            rows_consumos += f"""
            <tr style="background-color: {bg_color}; border-bottom: 1px solid #f0f0f0;">
                <td style="padding: 15px; color: #4b5563; font-size: 14px;">{c.producto}</td>
                <td style="padding: 15px; text-align: right; color: #111827; font-weight: 500; font-size: 14px;">${int(c.monto):,} COP</td>
            </tr>
            """
            
        html_factura = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
                * {{ font-family: 'Outfit', 'Segoe UI', Arial, sans-serif; }}
            </style>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f3f4f6;">
            <div style="max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 24px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.1); border: 1px solid #e5e7eb;">
                
                <!-- Luxury Header -->
                <div style="background-color: #1F1528; padding: 40px 20px; text-align: center; border-bottom: 4px solid #C5A059;">
                    <div style="color: #C5A059; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.3em; margin-bottom: 10px;">Experiencia Exclusiva</div>
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600; letter-spacing: 0.05em;">{config.nombre}</h1>
                    <div style="color: #9ca3af; font-size: 12px; margin-top: 10px;">{config.ciudad} • {config.direccion}</div>
                </div>

                <div style="padding: 40px;">
                    <!-- Invoice Info -->
                    <div style="text-align: center; margin-bottom: 40px;">
                        <div style="display: inline-block; padding: 8px 16px; background-color: #fef3c7; color: #92400e; border-radius: 20px; font-size: 12px; font-weight: 700; margin-bottom: 15px;">FACTURA ELECTRÓNICA</div>
                        <h2 style="margin: 0; color: #111827; font-size: 24px;">No. {factura.numero_factura}</h2>
                        <div style="color: #6b7280; font-size: 14px; margin-top: 5px;">Emitida el {datetime.now().strftime('%d de %B, %Y')}</div>
                    </div>

                    <!-- Guest Details -->
                    <div style="background-color: #f9fafb; padding: 25px; border-radius: 16px; margin-bottom: 35px; border: 1px solid #f3f4f6;">
                        <h3 style="margin-top: 0; color: #111827; font-size: 16px; border-bottom: 1px solid #e5e7eb; padding-bottom: 12px; margin-bottom: 15px;">Detalles del Huésped</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="color: #6b7280; font-size: 13px; padding: 4px 0;">Huésped</td>
                                <td style="color: #111827; font-size: 13px; font-weight: 600; text-align: right;">{reserva.nombre_cliente}</td>
                            </tr>
                            <tr>
                                <td style="color: #6b7280; font-size: 13px; padding: 4px 0;">Identificación</td>
                                <td style="color: #111827; font-size: 13px; font-weight: 600; text-align: right;">{reserva.cedula_nit}</td>
                            </tr>
                            <tr>
                                <td style="color: #6b7280; font-size: 13px; padding: 4px 0;">Habitación</td>
                                <td style="color: #111827; font-size: 13px; font-weight: 600; text-align: right;">#{habitacion.numero} ({habitacion.tipo})</td>
                            </tr>
                            <tr>
                                <td style="color: #6b7280; font-size: 13px; padding: 4px 0;">Estancia</td>
                                <td style="color: #111827; font-size: 13px; font-weight: 600; text-align: right;">{noches} Noches</td>
                            </tr>
                        </table>
                    </div>

                    <!-- Concepts Table -->
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                        <thead>
                            <tr style="border-bottom: 2px solid #1F1528;">
                                <th style="text-align: left; padding: 15px; color: #1F1528; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em;">Concepto</th>
                                <th style="text-align: right; padding: 15px; color: #1F1528; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em;">Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="border-bottom: 1px solid #f0f0f0;">
                                <td style="padding: 15px; color: #4b5563; font-size: 14px;">Servicios de Alojamiento</td>
                                <td style="padding: 15px; text-align: right; color: #111827; font-weight: 500; font-size: 14px;">${int(costo_alojamiento):,} COP</td>
                            </tr>
                            {rows_consumos}
                        </tbody>
                        <tfoot>
                            <tr>
                                <td style="padding: 25px 15px; font-size: 18px; font-weight: 400; color: #111827;">Total General</td>
                                <td style="padding: 25px 15px; text-align: right; font-size: 24px; font-weight: 700; color: #1F1528;">${int(factura.total):,} <span style="font-size: 14px; font-weight: 400; color: #6b7280;">COP</span></td>
                            </tr>
                        </tfoot>
                    </table>

                    <!-- Payment Proof -->
                    <div style="text-align: center; padding: 20px; background-color: #ecfdf5; border-radius: 12px; border: 1px solid #d1fae5; margin-bottom: 40px;">
                        <span style="color: #065f46; font-size: 14px; font-weight: 600;">✓ Pago Procesado Exitosamente</span>
                    </div>

                    <!-- Footer -->
                    <div style="text-align: center; border-top: 1px solid #e5e7eb; padding-top: 30px; color: #9ca3af; font-size: 12px;">
                        <p style="margin-bottom: 5px;">Este es un documento oficial emitido por {config.nombre}</p>
                        <p style="margin-bottom: 20px;">{config.email} • {config.web}</p>
                        <div style="color: #C5A059; font-size: 10px; font-weight: 700; text-transform: uppercase;">La Orquídea PMS • Gestión Hotelera Premium</div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return EmailService.enviar_correo(
            subject=f"OFICIAL: Su Factura de Estancia - {factura.numero_factura} - {config.nombre}",
            recipients=[reserva.email_cliente],
            html_body=html_factura
        )

    @staticmethod
    def enviar_codigo_reserva(reserva, habitacion, config):
        """Plantilla de confirmación con todos los datos de la reserva."""
        if not reserva.email_cliente:
            return False

        nombre_hotel = (config.nombre if config and config.nombre else "Hotel Boutique La Orquídea")
        num_hab = habitacion.numero if habitacion else "-"
        tipo_hab = habitacion.tipo if habitacion else ""
        try:
            noches = (reserva.fecha_fin - reserva.fecha_inicio).days
        except Exception:
            noches = 0
        try:
            total = float(reserva.total_pago or 0)
            total_fmt = f"${int(total):,} COP"
        except Exception:
            total_fmt = str(reserva.total_pago or "-")
        try:
            checkin = reserva.fecha_inicio.strftime('%d/%m/%Y')
            checkout = reserva.fecha_fin.strftime('%d/%m/%Y')
        except Exception:
            checkin, checkout = "-", "-"

        metodo = (reserva.metodo_pago or 'efectivo').lower()
        if metodo == 'nequi':
            if reserva.estado == 'pendiente_verificacion':
                pago_bloque = """
                    <div style="background-color: #fef9c3; padding: 20px; border-radius: 12px; border: 1px solid #fde68a; text-align: left; margin-bottom: 20px;">
                        <div style="color: #92400e; font-size: 14px; font-weight: 700;">⏳ Pago con Nequi: pendiente de verificación</div>
                        <div style="color: #92400e; font-size: 13px; margin-top: 6px;">Recibimos su comprobante. Nuestro personal validará el pago y le avisaremos. Su reserva está pre-confirmada.</div>
                    </div>"""
            else:
                pago_bloque = """
                    <div style="background-color: #ecfdf5; padding: 20px; border-radius: 12px; border: 1px solid #a7f3d0; text-align: left; margin-bottom: 20px;">
                        <div style="color: #065f46; font-size: 14px; font-weight: 700;">✓ Pago con Nequi registrado</div>
                    </div>"""
            metodo_label = "Nequi"
        elif metodo == 'efectivo':
            metodo_label = "Efectivo (pago al check-in)"
            pago_bloque = """
                    <div style="background-color: #eff6ff; padding: 20px; border-radius: 12px; border: 1px solid #bfdbfe; text-align: left; margin-bottom: 20px;">
                        <div style="color: #1e40af; font-size: 13px;">El pago en efectivo se realizará al momento del check-in en recepción.</div>
                    </div>"""
        else:
            metodo_label = reserva.metodo_pago or "Por confirmar"
            pago_bloque = ""

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="margin: 0; padding: 0; background-color: #f3f4f6;">
            <div style="max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 24px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.1); border: 1px solid #e5e7eb;">

                <div style="background-color: #1F1528; padding: 40px 20px; text-align: center; border-bottom: 4px solid #C5A059;">
                    <div style="color: #C5A059; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.3em; margin-bottom: 10px;">Confirmación de Reserva</div>
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600;">{nombre_hotel}</h1>
                </div>

                <div style="padding: 40px; text-align: center;">
                    <p style="color: #4b5563; font-size: 16px;">Estimado/a <strong>{reserva.nombre_cliente or 'huésped'}</strong>,</p>
                    <p style="color: #6b7280; font-size: 15px; line-height: 1.6;">Es un placer informarle que su reserva ha sido confirmada satisfactoriamente. Estamos preparando todo para su llegada.</p>

                    <div style="background-color: #f9fafb; padding: 35px; border-radius: 20px; border: 1px solid #f3f4f6; margin: 30px 0;">
                        <div style="color: #9ca3af; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.2em; margin-bottom: 15px;">Código de Acceso / Referencia</div>
                        <div style="font-size: 48px; font-weight: 700; color: #1F1528; letter-spacing: 0.1em;">{reserva.codigo}</div>
                    </div>

                    <div style="text-align: left; margin-bottom: 30px;">
                        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                            <tr style="border-bottom: 1px solid #f3f4f6;">
                                <td style="padding: 12px 0; color: #6b7280;">Huésped</td>
                                <td style="padding: 12px 0; text-align: right; color: #111827; font-weight: 600;">{reserva.nombre_cliente or '-'}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #f3f4f6;">
                                <td style="padding: 12px 0; color: #6b7280;">Habitación</td>
                                <td style="padding: 12px 0; text-align: right; color: #111827; font-weight: 600;">#{num_hab} ({tipo_hab})</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #f3f4f6;">
                                <td style="padding: 12px 0; color: #6b7280;">Check-in</td>
                                <td style="padding: 12px 0; text-align: right; color: #111827; font-weight: 600;">{checkin}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #f3f4f6;">
                                <td style="padding: 12px 0; color: #6b7280;">Check-out</td>
                                <td style="padding: 12px 0; text-align: right; color: #111827; font-weight: 600;">{checkout}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #f3f4f6;">
                                <td style="padding: 12px 0; color: #6b7280;">Noches</td>
                                <td style="padding: 12px 0; text-align: right; color: #111827; font-weight: 600;">{noches}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #f3f4f6;">
                                <td style="padding: 12px 0; color: #6b7280;">Precio total</td>
                                <td style="padding: 12px 0; text-align: right; color: #111827; font-weight: 600;">{total_fmt}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #f3f4f6;">
                                <td style="padding: 12px 0; color: #6b7280;">Método de pago</td>
                                <td style="padding: 12px 0; text-align: right; color: #111827; font-weight: 600;">{metodo_label}</td>
                            </tr>
                        </table>
                    </div>

                    {pago_bloque}

                    <div style="background-color: #fffbeb; padding: 20px; border-radius: 12px; border: 1px solid #fef3c7; text-align: left;">
                        <div style="color: #92400e; font-size: 13px; line-height: 1.5;">
                            <strong>Aviso Importante:</strong> Por favor, presente este código al momento de su llegada para agilizar su proceso de admisión.
                        </div>
                    </div>

                    <div style="margin-top: 40px; padding-top: 30px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 11px;">
                        <p>&copy; 2026 {nombre_hotel} • Gestión de Hospitalidad de Lujo</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        return EmailService.enviar_correo(
            subject=f"OFICIAL: Confirmación de Reserva #{reserva.codigo} - {nombre_hotel}",
            recipients=[reserva.email_cliente],
            html_body=html_body
        )

    @staticmethod
    def enviar_cancelacion_reserva(reserva, habitacion, config):
        if not reserva.email_cliente:
            return False
            
        nombre_hotel = config.nombre if config else "Hotel La Orquídea"
        num_hab = habitacion.numero if habitacion else "-"
        tipo_hab = habitacion.tipo if habitacion else ""
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
                * {{ font-family: 'Outfit', 'Segoe UI', Arial, sans-serif; }}
            </style>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f3f4f6;">
            <div style="max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 24px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.1); border: 1px solid #e5e7eb;">
                
                <div style="background-color: #1F1528; padding: 40px 20px; text-align: center; border-bottom: 4px solid #ef4444;">
                    <div style="color: #f87171; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.3em; margin-bottom: 10px;">Notificación de Cancelación</div>
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600;">{nombre_hotel}</h1>
                </div>

                <div style="padding: 40px; text-align: center;">
                    <p style="color: #4b5563; font-size: 16px;">Estimado/a <strong>{reserva.nombre_cliente}</strong>,</p>
                    <p style="color: #6b7280; font-size: 15px; line-height: 1.6;">Le confirmamos que su reserva con código <strong>{reserva.codigo}</strong> ha sido cancelada exitosamente.</p>
                    
                    <div style="background-color: #fef2f2; padding: 25px; border-radius: 16px; border: 1px solid #fecaca; margin: 25px 0; text-align: left;">
                        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                            <tr style="border-bottom: 1px solid #fee2e2;">
                                <td style="padding: 10px 0; color: #991b1b;">Habitación</td>
                                <td style="padding: 10px 0; text-align: right; color: #991b1b; font-weight: 600;">#{num_hab} ({tipo_hab})</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #fee2e2;">
                                <td style="padding: 10px 0; color: #991b1b;">Fechas Canceladas</td>
                                <td style="padding: 10px 0; text-align: right; color: #991b1b; font-weight: 600;">{reserva.fecha_inicio.strftime('%d/%m/%Y')} - {reserva.fecha_fin.strftime('%d/%m/%Y')}</td>
                            </tr>
                        </table>
                    </div>

                    <p style="color: #6b7280; font-size: 14px;">Esperamos volver a atenderle muy pronto en una próxima ocasión.</p>

                    <div style="margin-top: 40px; padding-top: 30px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 11px;">
                        <p>&copy; 2026 {nombre_hotel} • Gestión de Hospitalidad</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return EmailService.enviar_correo(
            subject=f"CANCELACIÓN DE RESERVA #{reserva.codigo} - {nombre_hotel}",
            recipients=[reserva.email_cliente],
            html_body=html_body
        )

from flask_mail import Message
from app import mail, db
from app.models import ConsumoPOS
from flask import render_template
from datetime import datetime

class EmailService:
    @staticmethod
    def enviar_correo(subject, recipients, html_body):
        try:
            from flask import current_app
            if not current_app.config.get('MAIL_USERNAME'):
                print("Saltando envío de correo: credenciales SMTP no configuradas.")
                return False

            sender = current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME')
            msg = Message(
                subject=subject,
                sender=sender,
                recipients=recipients,
                html=html_body
            )
            mail.send(msg)
            return True
        except Exception as e:
            print(f"Error enviando correo: {e}")
            return False

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
        if not reserva.email_cliente:
            return False
            
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
                
                <div style="background-color: #1F1528; padding: 40px 20px; text-align: center; border-bottom: 4px solid #C5A059;">
                    <div style="color: #C5A059; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.3em; margin-bottom: 10px;">Confirmación de Reserva</div>
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600;">{config.nombre}</h1>
                </div>

                <div style="padding: 40px; text-align: center;">
                    <p style="color: #4b5563; font-size: 16px;">Estimado/a <strong>{reserva.nombre_cliente}</strong>,</p>
                    <p style="color: #6b7280; font-size: 15px; line-height: 1.6;">Es un placer informarle que su reserva ha sido confirmada satisfactoriamente. Estamos preparando todo para su llegada.</p>
                    
                    <div style="background-color: #f9fafb; padding: 35px; border-radius: 20px; border: 1px solid #f3f4f6; margin: 30px 0;">
                        <div style="color: #9ca3af; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.2em; margin-bottom: 15px;">Código de Acceso / Referencia</div>
                        <div style="font-size: 48px; font-weight: 700; color: #1F1528; letter-spacing: 0.1em;">{reserva.codigo}</div>
                    </div>

                    <div style="text-align: left; margin-bottom: 30px;">
                        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                            <tr style="border-bottom: 1px solid #f3f4f6;">
                                <td style="padding: 12px 0; color: #6b7280;">Habitación</td>
                                <td style="padding: 12px 0; text-align: right; color: #111827; font-weight: 600;">#{habitacion.numero} ({habitacion.tipo})</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #f3f4f6;">
                                <td style="padding: 12px 0; color: #6b7280;">Fecha de Ingreso</td>
                                <td style="padding: 12px 0; text-align: right; color: #111827; font-weight: 600;">{reserva.fecha_inicio.strftime('%d/%m/%Y')}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #f3f4f6;">
                                <td style="padding: 12px 0; color: #6b7280;">Fecha de Salida</td>
                                <td style="padding: 12px 0; text-align: right; color: #111827; font-weight: 600;">{reserva.fecha_fin.strftime('%d/%m/%Y')}</td>
                            </tr>
                        </table>
                    </div>

                    <div style="background-color: #fffbeb; padding: 20px; border-radius: 12px; border: 1px solid #fef3c7; text-align: left;">
                        <div style="color: #92400e; font-size: 13px; line-height: 1.5;">
                            <strong>Aviso Importante:</strong> Por favor, presente este código al momento de su llegada para agilizar su proceso de admisión.
                        </div>
                    </div>

                    <div style="margin-top: 40px; padding-top: 30px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 11px;">
                        <p>&copy; 2026 {config.nombre} • Gestión de Hospitalidad de Lujo</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return EmailService.enviar_correo(
            subject=f"OFICIAL: Confirmación de Reserva #{reserva.codigo} - {config.nombre}",
            recipients=[reserva.email_cliente],
            html_body=html_body
        )

from flask_mail import Message
from app import mail, db
from app.models import ConsumoPOS
from flask import render_template

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
        if not reserva.email_huesped:
            return False
        
        noches = (reserva.fecha_salida - reserva.fecha_ingreso).days
        
        consumos = db.session.query(ConsumoPOS).filter_by(reservacion_id=reserva.id).all()
        total_extras = sum(c.monto for c in consumos)
        costo_alojamiento = factura.total - total_extras
        
        rows_consumos = ""
        for c in consumos:
            rows_consumos += f"<tr><td style='padding: 10px;'>{c.producto}</td><td style='padding: 10px; text-align: right;'>${{int(c.monto):,}} COP</td></tr>"
            
        html_factura = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ccc;">
            <div style="text-align: center; border-bottom: 2px solid #4a235a; padding-bottom: 15px; margin-bottom: 20px;">
                <h1 style="color: #1F1528; margin: 10px 0;">{config.nombre}</h1>
                <p>NIT: {config.nit}</p>
                <p>{config.direccion}, {config.ciudad}</p>
                <p>Tel: {config.telefono}</p>
            </div>
            
            <h2 style="background: #4a235a; color: white; padding: 10px; text-align: center;">FACTURA ELECTRÓNICA</h2>
            <p style="text-align: center; font-weight: bold;">No. {factura.numero_factura}</p>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <p><strong>Nombre:</strong> {reserva.nombre_huesped}</p>
                <p><strong>Documento:</strong> {reserva.tipo_documento}: {reserva.cedula_nit}</p>
                <p><strong>Habitación:</strong> {habitacion.numero} ({habitacion.tipo})</p>
                <p><strong>Estancia:</strong> {reserva.fecha_ingreso.strftime('%Y-%m-%d')} a {reserva.fecha_salida.strftime('%Y-%m-%d')} ({noches} noches)</p>
            </div>
            
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr style="background: #4a235a; color: white;">
                    <th style="padding: 10px; text-align: left;">Concepto</th>
                    <th style="padding: 10px; text-align: right;">Valor</th>
                </tr>
                <tr><td style='padding: 10px;'>Alojamiento ({noches} noches)</td>
                    <td style='padding: 10px; text-align: right;'>${int(costo_alojamiento):,} COP</td></tr>
                {rows_consumos}
                <tr style="background: #f8f9fa; font-weight: bold;">
                    <td style="padding: 15px;">TOTAL PAGADO</td>
                    <td style="padding: 15px; text-align: right; color: #4a235a; font-size: 18px;">${int(factura.total):,} COP</td>
                </tr>
            </table>
            
            <div style="text-align: center; margin-top: 20px; padding-top: 15px; border-top: 1px solid #ccc; font-size: 12px; color: #666;">
                <p>Gracias por su preferencia</p>
                <p>{config.nombre} - {config.ciudad}</p>
                <p>{config.email} - {config.web}</p>
            </div>
        </div>
        """
        
        return EmailService.enviar_correo(
            subject=f"Factura {factura.numero_factura} - {config.nombre}",
            recipients=[reserva.email_huesped],
            html_body=html_factura
        )

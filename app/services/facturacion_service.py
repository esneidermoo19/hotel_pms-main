from app.models import Factura, ConsumoPOS, ConfigHotel, Reservacion, Habitacion
from app import db
from datetime import datetime
from app.services.email_service import EmailService

class FacturacionService:
    @staticmethod
    def generar_numero_factura():
        ultima_factura = Factura.query.order_by(Factura.id.desc()).first()
        year = datetime.now().year
        if ultima_factura:
            try:
                # Intenta extraer el número secuencial
                ultimo_num = int(ultima_factura.numero_factura.split('-')[-1])
                return f"FACE-{year}-{(ultimo_num + 1):04d}"
            except (ValueError, IndexError):
                return f"FACE-{year}-{(ultima_factura.id + 1):04d}"
        else:
            return f"FACE-{year}-0001"

    @staticmethod
    def realizar_checkout(habitacion_id, metodo_pago):
        habitacion = Habitacion.query.get_or_404(habitacion_id)
        reserva = Reservacion.query.filter_by(habitacion_id=habitacion.id).order_by(Reservacion.id.desc()).first()
        
        if not reserva:
            raise ValueError('No se encontró una reserva activa para esta habitación.')

        config = ConfigHotel.query.first()
        if not config:
            config = ConfigHotel()
            db.session.add(config)
            db.session.commit()

        try:
            nuevo_numero = FacturacionService.generar_numero_factura()
            
            nueva_factura = Factura(
                reservacion_id=reserva.id,
                numero_factura=nuevo_numero,
                subtotal=reserva.total_pago,
                total=reserva.total_pago,
                nombre_cliente=reserva.nombre_huesped,
                nit_cliente=reserva.cedula_nit,
                tipo_documento=reserva.tipo_documento,
                metodo_pago=metodo_pago,
                estado='pagada',
                email_cliente=reserva.email_huesped
            )
            db.session.add(nueva_factura)
            db.session.flush()
            
            # Finalizar Reserva y Habitación
            reserva.estado = 'finalizada'
            habitacion.estado = 'Mantenimiento'
            
            db.session.commit()
            
            # Enviar correo si tiene email
            if reserva.email_huesped:
                enviado = EmailService.enviar_factura(nueva_factura, reserva, habitacion, config)
                if enviado:
                    nueva_factura.correo_enviado = True
                    db.session.commit()
                    
            return nueva_factura
            
        except Exception as e:
            db.session.rollback()
            raise e

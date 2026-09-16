-- Parche: columnas de estado de correo (arreglo envío de confirmación).
-- Idempotente: se puede ejecutar varias veces sin riesgo.
ALTER TABLE reservacion ADD COLUMN IF NOT EXISTS email_estado VARCHAR(20) DEFAULT 'pendiente';
ALTER TABLE reservacion ADD COLUMN IF NOT EXISTS email_error TEXT;
ALTER TABLE reservacion ADD COLUMN IF NOT EXISTS email_enviado_en TIMESTAMP;
ALTER TABLE reservacion ADD COLUMN IF NOT EXISTS email_intentos INTEGER DEFAULT 0;
-- Limpieza de parches antiguos (también idempotentes):
ALTER TABLE reservacion ADD COLUMN IF NOT EXISTS metodo_pago VARCHAR(50);
ALTER TABLE reservacion ADD COLUMN IF NOT EXISTS comprobante_pago VARCHAR(255);
ALTER TABLE config_hotel ADD COLUMN IF NOT EXISTS nequi_numero VARCHAR(30) DEFAULT '300 123 4567';
ALTER TABLE config_hotel ADD COLUMN IF NOT EXISTS nequi_qr VARCHAR(200) DEFAULT 'img/qr_nequi.png';

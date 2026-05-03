import sqlite3
import os

db_path = 'instance/hotel.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE reservacion ADD COLUMN metodo_pago VARCHAR(50)")
        print("Columna 'metodo_pago' añadida exitosamente.")
    except sqlite3.OperationalError as e:
        print(f"Nota: {e}")
    
    conn.commit()
    conn.close()
else:
    print(f"No se encontró la base de datos.")

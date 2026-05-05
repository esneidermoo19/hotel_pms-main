import sqlite3
import os

db_path = 'instance/hotel.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Intentar añadir la columna ip_address a reservacion
        cursor.execute("ALTER TABLE reservacion ADD COLUMN ip_address VARCHAR(45)")
        print("Columna 'ip_address' añadida exitosamente a la tabla 'reservacion'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("La columna 'ip_address' ya existe.")
        else:
            print(f"Error al añadir columna: {e}")
    
    conn.commit()
    conn.close()
else:
    print(f"No se encontró la base de datos en {db_path}")

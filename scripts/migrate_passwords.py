from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

def migrate_passwords():
    with app.app_context():
        users = User.query.all()
        migrated = 0
        for user in users:
            # Si el password_hash no contiene el prefijo de hashing de Werkzeug, lo hasheamos
            if not user.password_hash.startswith(('pbkdf2:', 'bcrypt:', 'scrypt:', 'argon2:')):
                print(f"Hasheando contraseña para el usuario: {user.username}")
                # Usamos el setter de la propiedad password que ya aplica el hash
                user.password = user.password_hash 
                migrated += 1
        
        if migrated > 0:
            db.session.commit()
            print(f"Migración completada. Se hashearon {migrated} contraseñas.")
        else:
            print("No se encontraron contraseñas en texto plano.")

if __name__ == '__main__':
    migrate_passwords()

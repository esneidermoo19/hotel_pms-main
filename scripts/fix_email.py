from app import create_app, db
from app.models import ConfigHotel

app = create_app()
with app.app_context():
    config = ConfigHotel.query.first()
    if config:
        print(f"EMAIL_IN_DB: {config.email}")
        config.email = 'laorquideahotel45@gmail.com'
        db.session.commit()
        print(f"UPDATED_TO: {config.email}")
    else:
        print("NO_CONFIG_FOUND")

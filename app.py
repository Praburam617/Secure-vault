import os
from app import create_app, db

app = create_app(os.getenv('FLASK_ENV', 'development'))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # host='0.0.0.0' allows connections from other devices (like mobile phones) on the same network
    app.run(host='0.0.0.0', port=5000, debug=True)

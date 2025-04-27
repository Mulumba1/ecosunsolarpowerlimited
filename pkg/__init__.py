from dotenv import load_dotenv
import os
from flask import Flask, g, session
from flask import Flask
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_mailman import Mail


load_dotenv()
migrate = Migrate()
csrf = CSRFProtect()
mail = Mail()



def create_app():
    from pkg.models import db, Admin
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile('config.py')
    app.config['BASE_DIR'] = app.root_path
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads') 
    db.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    migrate.init_app(app,db)
    @app.before_request
    def load_admin():
        admin_id = session.get('admin_id')
        g.admin = Admin.query.get(admin_id) if admin_id else None
    return app

app = create_app()

from pkg import admin_routes, user_routes
import os
from flask import Flask
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_app():
    app = Flask(__name__, static_folder='static')

    # Load secret key from environment variables
    app.secret_key = os.getenv("SECRET_KEY")

    from .controllers.emails import emails_bp

    # Import and register blueprints
    from .controllers import auths, content, reports, emails, optimizes

    app.register_blueprint(auths.auths_bp)
    app.register_blueprint(emails_bp, url_prefix='/emails')
    app.register_blueprint(optimizes.optimize_bp)

    app.register_blueprint(content.content_bp)
    app.register_blueprint(reports.reports_bp)
   
    return app

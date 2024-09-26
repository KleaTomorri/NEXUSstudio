from flask import Blueprint, render_template, redirect, request, session, flash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_bcrypt import Bcrypt
from flask_app.models.auth import User


content_bp = Blueprint('content', __name__)
bcrypt = Bcrypt()


@content_bp.route('/generate-content')
def dashboard():
    return render_template('generate_content.html')




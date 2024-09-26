import os
from flask import Blueprint, render_template, redirect, request, session, flash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_bcrypt import Bcrypt
from flask_app.models.auth import User
from dotenv import load_dotenv

load_dotenv()

auths_bp = Blueprint('auths', __name__)
bcrypt = Bcrypt()

# Use environment variables for sensitive data
s = URLSafeTimedSerializer(os.getenv("SECRET_KEY"))
password_reset_salt = os.getenv("PASSWORD_RESET_SALT")

@auths_bp.route('/')
def dashboard():
    return render_template('dashboard.html')

@auths_bp.route('/edit-profile')
def edit_profile():
    user = session.get('user')
    return render_template('profile.html', user=user)

@auths_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if not User.validate_userRegister(request.form):
            return redirect(request.referrer)

        existing_user = User.get_user_by_email({'email': request.form['email']})
        if existing_user:
            flash("Email already registered. Please log in or use a different email.", 'emailRegister')
            return redirect(request.referrer)

        session['register_data'] = {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'email': request.form['email'],
            'password': bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        }

        verification_code = User.generate_verification_code()
        session['verification_code'] = verification_code
        session['user_email'] = request.form['email']

        if User.send_verification_email(request.form['email'], verification_code):
            flash("A verification code has been sent to your email.", 'verification')
        else:
            flash("Error sending verification email. Please try again later.", 'verification')

        return redirect('/confirm_email')

    return render_template('register.html')

@auths_bp.route('/confirm_email', methods=['GET', 'POST'])
def confirm_email():
    if request.method == 'POST':
        entered_code = request.form['confirmation_code']
        stored_code = session.get('verification_code')

        if stored_code and entered_code == str(stored_code):
            user_data = session.pop('register_data', None)
            if user_data:
                data = {
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'email': user_data['email'],
                    'password': user_data['password'],
                    'is_verified': True  
                }
                User.create(data)
                session.pop('verification_code', None)
                session.pop('user_email', None)
                flash('Your email has been verified. You are now logged in.', 'verification')

                user = User.get_user_by_email({'email': user_data['email']})
                session['user_id'] = user['id']
                session['user_email'] = user['email']
                session['user_first_name'] = user['first_name']
                session['user_last_name'] = user['last_name']
                session['user_initials'] = f"{user['first_name'][0]}{user['last_name'][0]}"

                return redirect('/home')
        else:
            flash('Incorrect confirmation code. Please try again.', 'verification')
            return redirect(request.referrer)

    return render_template('confirm_email.html')

@auths_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')

        user_data = User.get_user_by_email({'email': email})
        if not user_data:
            flash('User does not exist. Please register.', 'loginError')
            return redirect(request.referrer)

        user = User(user_data)
        if not user.verified:
            flash('Email not verified. Please check your email.', 'loginError')
            return redirect(request.referrer)

        if not bcrypt.check_password_hash(user.password, password):
            flash('Incorrect password. Please try again.', 'loginError')
            return redirect(request.referrer)

        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_first_name'] = user.first_name
        session['user_last_name'] = user.last_name
        session['user_initials'] = f"{user.first_name[0]}{user.last_name[0]}"

        if remember:
            session.permanent = True

        return redirect('/home')

    return render_template('login.html')

@auths_bp.route('/home')
def home():
    if 'user_id' not in session:
        return redirect('/')

    return render_template('home.html')

@auths_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@auths_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user_data = User.get_user_by_email({'email': email})
        if not user_data:
            flash('Email not found. Please register.', 'forgotPasswordError')
            return redirect(request.referrer)

        user = User(user_data)
        token = s.dumps(user.email, salt=password_reset_salt)
        reset_url = f"http://localhost:5000/reset_password/{token}"
        User.send_password_reset_email(user.email, reset_url)

        flash('A password reset link has been sent to your email.', 'forgotPasswordSuccess')
        return redirect('/login')

    return render_template('forgot_password.html')

@auths_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt=password_reset_salt, max_age=3600)
    except SignatureExpired:
        flash('The password reset link has expired.', 'resetPasswordError')
        return redirect('/forgot_password')

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash('Passwords do not match.', 'resetPasswordError')
            return redirect(request.referrer)

        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        User.update_password({'email': email, 'password': hashed_password})

        flash('Your password has been reset. You can now log in.', 'resetPasswordSuccess')
        return redirect('/login')

    return render_template('reset_password.html', token=token)

@auths_bp.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect('/login')

    # Validate the form data
    if not User.validate_user_update(request.form):
        return redirect(request.referrer)

    data = {
        'id': session['user_id'],
        'first_name': request.form['first_name'],
        'last_name': request.form['last_name'],
        'email': request.form['email']
    }

    # Check if email is being changed and if it already exists
    existing_user = User.get_user_by_email({'email': request.form['email']})
    if existing_user and existing_user['id'] != session['user_id']:
        flash("Email already taken by another user.", 'emailUpdateError')
        return redirect(request.referrer)

    # Update the user's details in the database
    User.update(data)

    # Update session information
    session['user_first_name'] = data['first_name']
    session['user_last_name'] = data['last_name']
    session['user_email'] = data['email']
    session['user_initials'] = f"{data['first_name'][0]}{data['last_name'][0]}"

    flash("Profile updated successfully.", 'profileUpdateSuccess')
    return redirect('/home')

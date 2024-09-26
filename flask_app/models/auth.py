from flask_app.config.mysqlconnection import connectToMySQL
from flask import flash
import re
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from itsdangerous import URLSafeTimedSerializer

from dotenv import load_dotenv
import os


load_dotenv()

s = URLSafeTimedSerializer("SECRET_KEY")

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
PASSWORD_REGEX = re.compile(r'^(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z0-9]).{8,}$')

class User:
    DB = "interviews"

    def __init__(self, data):
        self.id = data['id']
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        self.email = data['email']
        self.password = data['password']
        self.created_at = data['created_at']
        self.verified = data['verified']

    @classmethod
    def get_user_by_email(cls, data):
        query = 'SELECT * FROM users WHERE email = %(email)s;'
        result = connectToMySQL(cls.DB).query_db(query, data)
        return result[0] if result else False

    @classmethod
    def create(cls, data):
        query = 'INSERT INTO users (first_name, last_name, email, password, verified) VALUES (%(first_name)s, %(last_name)s, %(email)s, %(password)s, %(is_verified)s);'
        return connectToMySQL(cls.DB).query_db(query, data)

    @staticmethod
    def validate_user(user):
        is_valid = True
        if not EMAIL_REGEX.match(user['email']):
            flash("Invalid email address!", 'emailLogin')
            is_valid = False
        if len(user['password']) < 8:
            flash("Password must be at least 8 characters long!", 'passwordLogin')
            is_valid = False
        return is_valid

    @staticmethod
    def validate_userRegister(user):
        is_valid = True
        if not EMAIL_REGEX.match(user['email']):
            flash("Invalid email address!", 'emailRegister')
            is_valid = False
        if not PASSWORD_REGEX.match(user['password']):
            flash("Password must contain at least 8 characters, one uppercase letter, one number, and one special character.", 'passwordRegister')
            is_valid = False
        if len(user['first_name']) < 1:
            flash("First name is required!", 'nameRegister')
            is_valid = False
        if len(user['last_name']) < 1:
            flash("Last name is required!", 'lastNameRegister')
            is_valid = False
        return is_valid

    @staticmethod
    def send_verification_email(email, code):
        
        sender_email = os.getenv("EMAIL_ADDRESS")
        password = os.getenv("EMAIL_PASSWORD")
        receiver_email = email
        

        message = MIMEMultipart()
        message["Subject"] = "Email Verification Code"
        message["From"] = sender_email
        message["To"] = receiver_email

        body = f"Your verification code is: {code}"
        message.attach(MIMEText(body, "plain"))

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            server.quit()
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    @staticmethod
    def generate_verification_code():
        return random.randint(100000, 999999)



    @staticmethod
    def send_password_reset_email(email, reset_url):
        
        sender_email = os.getenv("EMAIL_ADDRESS")
        password = os.getenv("EMAIL_PASSWORD")
        receiver_email = email
        

        message = MIMEMultipart()
        message["Subject"] = "Password Reset Request"
        message["From"] = sender_email
        message["To"] = receiver_email

        body = f"To reset your password, click the following link: {reset_url}"
        message.attach(MIMEText(body, "plain"))

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            server.quit()
        except Exception as e:
            print(f"Error sending email: {e}")

    @classmethod
    def update_password(cls, data):
        query = 'UPDATE users SET password = %(password)s WHERE email = %(email)s;'
        return connectToMySQL(cls.DB).query_db(query, data)
    
    
    
    
    @classmethod
    def update(cls, data):
        query = """
        UPDATE users
        SET first_name = %(first_name)s, last_name = %(last_name)s, email = %(email)s
        WHERE id = %(id)s;
        """
        return connectToMySQL(cls.DB).query_db(query, data)

    
    
    @staticmethod
    def validate_user_update(user):
        is_valid = True
        if len(user['first_name']) < 1:
            flash("First name is required!", 'nameUpdate')
            is_valid = False
        if len(user['last_name']) < 1:
            flash("Last name is required!", 'lastNameUpdate')
            is_valid = False
        if not EMAIL_REGEX.match(user['email']):
            flash("Invalid email address!", 'emailUpdate')
            is_valid = False
        return is_valid

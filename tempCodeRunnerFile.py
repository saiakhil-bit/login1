from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
import random
import string
from flask_mail import Mail, Message
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

# Database Configuration (Supabase URL from .env)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')  # Gmail address
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # Gmail App Password
mail = Mail(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    college = db.Column(db.String(100), nullable=False)

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        return render_template('home.html', user_name=session['user_name'])
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        college = request.form.get('college')

        # Check if the email is already registered
        if User.query.filter_by(email=email).first():
            flash('Email already registered!')
            return redirect('/register')

        # Save the new user to the database
        new_user = User(name=name, email=email, password=password, college=college)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash(f'Welcome, {user.name}!')
            return redirect('/')
        else:
            flash('Invalid email or password!')
            return redirect('/login')

    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if not user:
            flash('Email not registered!')
            return redirect('/forgot-password')

        # Generate a temporary password
        temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        user.password = temp_password
        db.session.commit()

        # Send reset password email
        msg = Message('Password Reset Request',
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[email])
        msg.body = f'Your new password is: {temp_password}. Please log in and change it immediately.'

        try:
            mail.send(msg)
            flash(f'Password reset email sent to {email}.')
            return redirect('/login')
        except Exception as e:
            flash(f'Failed to send email: {str(e)}')
            return redirect('/forgot-password')

    return render_template('forgot_password.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect('/login')

# Initialize the database
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    from os import environ
    app.run(host="0.0.0.0", port=int(environ.get("PORT", 5000)))

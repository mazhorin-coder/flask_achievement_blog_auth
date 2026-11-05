import os
import secrets
from flask import Flask, render_template, redirect, request, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta, timezone

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///blog.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "super-secret-key-for-flask-app-2026"

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Notes(db.Model):
    __tablename__ = "notes"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    subtitle = db.Column(db.String(150), nullable=True)
    text = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<Note {self.title}>"

class Users(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=True)

    def check_password(self, password):
        return self.password == password

@app.route('/')
def home():
    topics_data = [
        {"title": "Тема 1. Основы Flask", "progress": "100%", "hw": "100%", "comment": "Изучены основы Flask, приложение успешно запущено."},
        {"title": "Тема 2. HTML & CSS", "progress": "100%", "hw": "100%", "comment": "Шаблоны и стили полностью настроены."},
        {"title": "Тема 3. Шаблоны и формы в Flask", "progress": "100%", "hw": "100%", "comment": "Изучены наследование и формы в Flask."},
        {"title": "Тема 4. Основы Flask-SQLAlchemy...", "progress": "100%", "hw": "100%", "comment": "Настроена база данных SQLite, создана модель Notes и выполнены миграции."},
        {"title": "Тема 5. Авторизация в Flask", "progress": "100%", "hw": "100%", "comment": "Реализована система авторизации с использованием токенов и сессий."},
        {"title": "Тема 6. Работа с REST API", "progress": "0%", "hw": "0%", "comment": ""},
        {"title": "Тема 7. Итоговый проект", "progress": "0%", "hw": "-", "comment": ""},
        {"title": "Итоговая аттестация", "progress": "0%", "hw": "0%", "comment": ""},
    ]
    return render_template('index.html', topics=topics_data)


@app.route('/notes', methods=['GET', 'POST'])
def notes():
    if request.method == 'POST':
        title = request.form.get('title')
        subtitle = request.form.get('subtitle')
        text = request.form.get('text')

        if title and text:
            new_note = Notes(title=title, subtitle=subtitle, text=text)
            db.session.add(new_note)
            db.session.commit()

        return redirect(url_for('notes'))

    all_notes = Notes.query.all()
    return render_template('notes.html', notes=all_notes)

@app.route('/home')
def guest_home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    user_exists = Users.query.filter((Users.username == username) | (Users.email == email)).first()
    if user_exists:
        flash("Пользователь с таким логином или email уже существует.", "error")
        return redirect(url_for('register'))

    new_user = Users(username=username, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()

    flash("Вы успешно зарегистрировались! Пожалуйста, войдите.", "success")
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form.get('username')
    password = request.form.get('password')

    user = Users.query.filter_by(username=username).first()
    if user and user.check_password(password):
        token = secrets.token_hex(16)
        user.token = token
        db.session.commit()

        session["token"] = token
        expiration_time = datetime.now(timezone.utc) + timedelta(minutes=30)
        session["expiration"] = expiration_time.isoformat()
        flash("Вы успешно вошли в систему!", "success")
        return redirect(url_for('home'))
    else:
        flash("Неверный логин или пароль.", "error")
        return redirect(url_for('login'))

@app.before_request
def check_authentication():
    if request.endpoint in ['login', 'register', 'guest_home', 'static'] or not request.endpoint:
        return

    token = session.get("token")
    expiration_str = session.get("expiration")

    is_expired = True
    if expiration_str:
        expiration_time = datetime.fromisoformat(expiration_str)
        if datetime.now(timezone.utc) < expiration_time:
            is_expired = False

    if not token or is_expired:
        session.clear()
        return redirect(url_for("guest_home"))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('guest_home'))

if __name__ == "__main__":
    app.run(debug=True)
import logging

from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, UserMixin, login_required, login_user, current_user

from config import dev
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(dev)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(message)s')

admin = Admin(app)

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(128))
    avatar_hash = db.Column(db.String(32))


@login_manager.user_loader
def load_user(user_id):
    # user = User.query.get(user_id)
    user = User()
    return user


import logging
from flask import render_template, request, session, redirect, url_for
import random
from app import app

db.create_all()


class BaseModeView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated


admin.add_view(BaseModeView(User, db.session))


@app.route('/')
@login_required
def index():
    logging.info("aaa 1111111")
    print("1111")

    user = User()
    user.name = "123"
    db.session.add(user)
    db.session.commit()

    users = User.query.all()
    logging.info(users)

    return f"session id =   {session['user_id']} random={random.randint(1,100)}"


@app.route('/login/', methods=['POST', 'GET'])
def login():
    if request.method == 'POST' or True:
        logging.info("aaa")
        # logging.info(request.form)
        # session['username'] = request.form['username']
        #session['user_id'] = random.randint(1,  100)
        #return redirect(url_for('index'))

        # if check successfully..
        user = User()
        login_user(user)
        return "login page"

    return render_template('login.html')


@app.route('/logout/')
@login_required
def logout():
    session.clear()
    return "logout done"



if __name__ == '__main__':
    app.run()

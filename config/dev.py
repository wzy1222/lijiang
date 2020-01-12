# config.py
# encoding:utf-8
from sqlalchemy import create_engine

DEBUG = True
SECRET_KEY = b'#"F4Q8z\n\xec]/66241'


USERNAME = "root"
PASSWORD = "rootroot"
HOST = "127.0.0.1"
PORT = "3306"
DATABASE = "test"
DB_URI = "mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8".format(USERNAME, PASSWORD,
                                                      HOST, PORT, DATABASE)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# SQLALCHEMY_DATABASE_URI = DB_URI
SQLALCHEMY_BINDS = {
    'test': DB_URI
}
engine = create_engine(DB_URI, echo=True)


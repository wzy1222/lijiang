# config.py
# encoding:utf-8
# from flask_sqlalchemy import create_engine
from sqlalchemy import create_engine

DEBUG = True
SECRET_KEY = b'#"F4Q8z\n\xec]/66241'


USERNAME = "coroyeah"
PASSWORD = "coroyeahWENZHU2018"
HOST = "rm-j6cy632s227w9w6r9.mysql.rds.aliyuncs.com"
PORT = "3306"
DATABASE = "lijiang"
DB_URI = "mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8mb4".format(USERNAME, PASSWORD,
                                                      HOST, PORT, DATABASE)
SQLALCHEMY_DATABASE_URI = DB_URI

SQLALCHEMY_TRACK_MODIFICATIONS = False

# SQLALCHEMY_DATABASE_URI = DB_URI
SQLALCHEMY_BINDS = {
     DATABASE: DB_URI
}
engine = create_engine(DB_URI, echo=True)


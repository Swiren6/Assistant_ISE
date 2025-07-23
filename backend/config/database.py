from flask_mysqldb import MySQL
import os

mysql = MySQL()

def init_db(app):
    """Initialise la configuration MySQL"""
    app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
    app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
    app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
    app.config['MYSQL_DB'] = os.getenv('MYSQL_DATABASE')
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
    
    mysql.init_app(app)
    return mysql

def get_db_connection():
    """Retourne une connexion à la base de données"""
    return mysql.connection
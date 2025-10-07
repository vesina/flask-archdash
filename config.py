from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))

class Config:
 
    SECRET_KEY = environ.get('SECRET_KEY')
    FLASK_APP = environ.get('FLASK_APP')
    FLASK_ENV = environ.get('FLASK_ENV')

    SQLALCHEMY_DATABASE_URI = 'sqlite:///local.db' #f'mssql+pyodbc://{server}/{catalog}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes' #
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    starr_db = 'leap_data_starr'
    wdm_db = 'wdm_stg'

    SQLALCHEMY_BINDS = {
        "starr_dev": f'mssql+pyodbc://m1-starrsql01d/{starr_db}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes',
        "starr_test": f'mssql+pyodbc://m1-starrsql01t/{starr_db}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes',
        "starr_prod": f'mssql+pyodbc://m1-starrsql01/{starr_db}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes',
        "wdm_dev": f'mssql+pyodbc://m1-wdmsql01d/{wdm_db}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes',
        "wdm_test": f'mssql+pyodbc://m1-wdmsql01t/{wdm_db}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes',
        "wdm_prod": f'mssql+pyodbc://m1-wdmsql01/{wdm_db}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes',
    }

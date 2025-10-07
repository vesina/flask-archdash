from sqlalchemy import text, create_engine
import pandas as pd 

from config import Config

def get_url(key: str):
    return Config.SQLALCHEMY_BINDS[key]

 
def exec_procedure_json(qry: str, conn_key: str=None):
    if conn_key is None or conn_key == "":
        url =  Config.SQLALCHEMY_DATABASE_URI
    else:
        url = Config.SQLALCHEMY_BINDS[conn_key]
    engine = create_engine(url)
    with engine.connect() as conn:
        result = conn.execute(text(qry))
        res = result.fetchall()
        conn.close()
        return res

def exec_procedure(qry: str, conn_key: str=None):
    if conn_key is None or conn_key == "":
        url =  Config.SQLALCHEMY_DATABASE_URI
    else:
        url = Config.SQLALCHEMY_BINDS[conn_key]
    engine = create_engine(url)
    with engine.connect() as conn:
        df = pd.read_sql(qry, conn)
        conn.close()
        return df
    
def exec_procedure_json_2(qry: str, url: str):

    engine = create_engine(url)
    with engine.connect() as conn:
        result = conn.execute(text(qry))
        res = result.fetchall()
        conn.close()
        return res

def exec_procedure_2(qry: str, url: str):

    engine = create_engine(url)
    with engine.connect() as conn:
        df = pd.read_sql(qry, conn)
        conn.close()
        return df
 
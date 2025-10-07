from fileinput import filename
from venv import logger
from flask import Flask, request, jsonify, redirect, abort, session, url_for
from flask import current_app, g
import pyodbc
import pandas as pd
import requests
import os
# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy.orm import DeclarativeBase
# from flask.templating import render_template

 
from dbquery import exec_procedure, exec_procedure_json, exec_procedure_2, exec_procedure_json_2
from sqlconfig import *
from models import User, db, Report, Server
import sqlconfig


from flask import Flask, render_template
import plotly.express as px
from plotly import utils
import json

from flask_login import LoginManager
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# from werkzeug.security import generate_password_hash, check_password_hash
# from flask_login import UserMixin

import archdash as arc
# create the app
app = Flask(__name__)
app.secret_key = 'kjadflkjfladjsfjasadsk'

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI #'sqlite:///local.db' #f'mssql+pyodbc://{server}/{catalog}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes' #
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS #False
app.config["SQLALCHEMY_BINDS"] = SQLALCHEMY_BINDS
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

db.init_app(app)
with app.app_context():
    db.create_all()

print(f'App initialized: {app}\n{db}')
print(f'App initialized: {SQLALCHEMY_DATABASE_URI}')

# added login manager    
login_manager.init_app(app)
login_manager.login_view = 'login' # Specify the login route

print('App login initialized')

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

@app.route('/')
def index():
    if 'username' in session:
        return f'Logged in as {session["username"]}'
    return 'You are not logged in'

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         session['username'] = request.form['username']
#         return redirect(url_for('index'))
#     return '''
#         <form method="post">
#             <p><input type=text name=username>
#             <p><input type=submit value=Login>
#         </form>
#     '''

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('index'))

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if current_user.is_authenticated:
#         return redirect(url_for('index'))
#     if request.method == 'POST':
#         username = request.form.get('username')
#         password = request.form.get('password')
#         user = User.query.filter_by(username=username).first()
#         if user:
#             flash('Username already exists.')
#             return redirect(url_for('register'))
#         new_user = User(username=username)
#         new_user.set_password(password)
#         db.session.add(new_user)
#         db.session.commit()
#         flash('Registration successful! Please log in.')
#         return redirect(url_for('login'))
#     return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        if current_user.is_authenticated:
            return f'Hello, {current_user.username}!'
        else: 
            return 'Hello guest!'
        # return render_template('archdash.html', title=f'Archdash Home Page', username=current_user.uername, memo=f"Logged in as user {current_user.username}")
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            session['username'] = request.form['username']
            return render_template('archdash.html', title=f'Archdash Home Page', user=current_user)
        else:
            flash('Invalid username or password.')
    return render_template('login.html')

# @app.route('/logout')
# @login_required
# def logout():
#     logout_user()
#     return redirect(url_for('index'))

# @app.route('/archdash')
# @login_required
# def dashboard():
#     return f'Welcome, {current_user.username}!'

# @app.route('/')
# def index():
#     return render_template('index.html')

@app.route('/archdash/')
# @login_required
def get_archdash_ds():
    return render_template('archdash.html', title=f'Archdash Home Page')

@app.route('/archdash/project/')
# @login_required
def get_archdash_project():
    df = arc.get_project_data(csvfile=arc.project_file)
    fig = arc.get_project_figure(df)
    graphJSON = json.dumps(fig, cls=utils.PlotlyJSONEncoder)

    return render_template('archdash.html', graphJSON=graphJSON, title=f'Project Data Chart')

@app.route('/archdash/usage/<label>')
# @login_required
def get_archdash_usage(label: str):
    fdf = arc.load_benchmark_file(csvfile=arc.benchmark_file)

    ## show Electrical usage
    if label.lower() == "electricity" or label.lower() == "el" or label.lower() == "electric":
        lbl = "Electricity"
        usage_df= arc.get_usage_data(data=fdf, monthlist=arc.MONTHLIST_EL, debug=False)    

    # show natural gas usage
    elif label.lower() == "gas" or label.lower() == "naturalgas" or label.lower() == "natural-gas":
        lbl = "Natural Gas"
        usage_df= arc.get_usage_data(data=fdf, monthlist=arc.MONTHLIST_GAS, debug=False)  

    title = f'Building Type vs. Median Monthly {lbl} Use per SQFT'
    yaxis_title = f'Building Type vs. Median Monthly {lbl} Use per SQFT'
   
    fig = arc.get_usage_figure(df=usage_df, title=title, yaxistitle=yaxis_title)
    graphJSON = json.dumps(fig, cls=utils.PlotlyJSONEncoder)    

    return render_template('archdash.html', graphJSON=graphJSON, title=f'Monthly {lbl} Usage Chart')


@app.route('/api/results/<report_id>',defaults={'server_key': None, 'forjson': 'table'})
@app.route('/api/results/<report_id>',defaults={'server_key': None})
@app.route('/api/results/<report_id>,<server_key>,<forjson>')
@app.route('/api/results/<report_id>,<server_key>')
def api_get_report_results(report_id, server_key, forjson: str='table'):
    try:
        # data = Report.query.get(report_id)
        data = db.session.get(Report,report_id)
        # report['report_proc'] for r in reports if r['report_id'] == report_id]
        report_proc =  data.report_proc #'RPT.get_submission_results_status' #report['report_proc']
        if server_key:
            key = server_key
        else:
            key = 'starr_dev'

        qry = f'exec {report_proc}'                                                     
        
        if forjson == 'json':  
            result = exec_procedure_json(qry, key)      
            return jsonify(result)
        else:         
            df = exec_procedure(qry, key)     
            df2=df.set_index(df.columns[1])
            return jsonify(df2.to_dict('records'))
    except Exception:
        abort(504)

@app.route('/api/results/<report_id>,<server>,<catalog>,<forjson>')
def api_get_report_results_2(report_id, server, catalog, forjson: str='json'):
    try:
        # data = Report.query.get(report_id)
        url = sqlconfig.get_url(server, catalog)
        data = db.session.get(Report,report_id)
        # report['report_proc'] for r in reports if r['report_id'] == report_id]
        report_proc =  data.report_proc #'RPT.get_submission_results_status' #report['report_proc']

        qry = f'exec {report_proc}'                                                     
        
        if forjson == 'json':  
            result = exec_procedure_json_2(qry, url)      
            return jsonify(result)
        else:         
            df = exec_procedure_2(qry, url)     
            df2=df.set_index(df.columns[1])
            return jsonify(df2.to_dict('records'))
    except Exception:
        abort(504)

@app.route('/api/reports')
@app.route('/api/reports/')
def api_get_reports():
    reports = Report.query.all()
    return  jsonify([report.to_json() for report in reports])

@app.route('/api/reports/<report_id>')
def api_get_report(report_id):
    report_data = Report.query.get(report_id)
    return jsonify(Report.to_json(report_data)), 200


@app.route('/reports/')
@app.route('/reports/<int:report_id>')
def get_reports(report_id=None):
    if report_id:
        data = Report.query.get(report_id)
        return render_template('reports/report.html',data=data), 200
    else:
        data = Report.query.all()
        # data = db.session.get(Report,2)
        return render_template('reports/reports.html', data=data), 200
   

@app.route('/remove-report/<int:report_id>')
def remove_report(report_id):
    try:
        data = Report.query.get(report_id)        
        db.session.delete(data)
        db.session.commit()
        return redirect('../reports') 
    except Exception as ex:
        abort(404)

# @app.route('/html/<report_id>',defaults={'server_key': None})
@app.route('/html/<report_id>,<server_key>')
def get_html_report(report_id, server_key):
    if server_key:
        key = server_key
    else:
        key = 'starr_dev'

    url = f'http://localhost:5000/api/results/{report_id},{key},table'
    # return url
    result = requests.get(url)
    # return result.json()
    df= pd.DataFrame(result.json())
    return df.to_html()
 


@app.route('/add-report',methods=["GET","POST"])
def register_report():
    if request.method == "POST":
        report_name = request.form.get('report_name')
        report_proc = request.form.get('report_proc')
        report_params = request.form.get('report_params')
        if report_name != '':
            report = Report(report_name=report_name, report_proc=report_proc, report_params=report_params)
            db.session.add(report)
            db.session.commit()
        return redirect('reports') 
    else:
        return render_template('reports/add_report.html') 
    
@app.route('/run-report',methods=["GET","POST"])
def run_report():
    if request.method == "POST":
        report_name = request.form.get('report_name')
        report_proc = request.form.get('report_proc')
        report_params = request.form.get('report_params')
        server_name = request.form.get('server_name')
        catalog = request.form.get('catalog')
        if report_name != '':
            report = Report(report_name=report_name, report_proc=report_proc, report_params=report_params)
            db.session.add(report)
            db.session.commit()
        return redirect('reports') 
    else:
        return render_template('reports/add_report.html') 
    #jsonify(data), 201




if __name__ == '__main__':
    app.run(debug=True)
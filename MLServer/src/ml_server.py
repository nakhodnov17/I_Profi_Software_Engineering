import os
import pickle
import datetime

import numpy as np

import plotly
import plotly.subplots
import plotly.graph_objects as go
from shapely.geometry.polygon import Point
from shapely.geometry.polygon import Polygon

from collections import namedtuple
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from flask import Flask, request, url_for
from flask import render_template, redirect

from flask_wtf.file import FileAllowed
from wtforms.validators import DataRequired
from wtforms import StringField, SubmitField, FileField, SelectField, HiddenField

from utils import polygon_random_point


app = Flask(__name__, template_folder='html')
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
app.config['SECRET_KEY'] = 'hello'
data_path = './../artefacts'
Bootstrap(app)
messages = []

all_users = dict()


class Data:
    def __init__(self, data_name, data_type, data_path, data_request, **kwargs):
        self.data_name = data_name
        self.data_type = data_type
        self.data_path = data_path
        self.data_request = data_request
        self.options = kwargs


class UserData:
    def __init__(self, username, password):
        self.username = username
        self.password = password

        self.data_sources = dict()


class AuthForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = StringField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class SelectTypeForm(FlaskForm):
    username = HiddenField("username")

    datatype = SelectField(
        'Источник данных', choices=['csv', 'xls', 'postgresql', 'mongodb'], validators=[DataRequired()]
    )
    submit = SubmitField('Создать')


class GoToPipeline(FlaskForm):
    username = HiddenField("username")
    data_name = StringField('Название датасета', validators=[DataRequired()])
    submit = SubmitField('Перейти к созданию пайплайна')


class CSVFileForm(FlaskForm):
    username = HiddenField("username")

    data_name = StringField('Название датасета', validators=[DataRequired()])
    file_path = StringField('Путь к файлу', validators=[DataRequired()])
    separator = StringField('Сепаратор', validators=[DataRequired()], default=',')
    submit = SubmitField('Добавить файл')


class CreateModel(FlaskForm):
    username = HiddenField("username")
    data_name = HiddenField("data_name")

    model_type = SelectField(
        'Тип модели', choices=['SARIMA', 'DBSCAN', 'Anomaly detection'], validators=[DataRequired()]
    )
    submit = SubmitField('Обучить')


@app.route('/', methods=['GET', 'POST'])
def auth_page():
    try:
        auth_form = AuthForm()
        if auth_form.validate_on_submit():
            username = auth_form.username.data
            password = auth_form.password.data
            print('LLL', username)
            # Check auth
            if username in all_users:
                pass
            else:
                all_users[username] = UserData(username, password)

            return redirect(url_for('show_data', username=username))
        else:
            return render_template('from_form.html', form=auth_form)
    except Exception as exc:
        app.logger.info('Exception: {0}'.format(exc))


@app.route('/show_data', methods=['GET', 'POST'])
def show_data():
    try:
        username = request.args.get('username')
        data_types_form = SelectTypeForm(username=username)
        go_to_pipeline = GoToPipeline(username=username)
        if data_types_form.validate_on_submit():
            datatype = data_types_form.datatype.data
            username = data_types_form.username.data

            if datatype == 'csv':
                return redirect(url_for('add_csv', username=username))
            elif datatype == 'xml':
                return redirect(url_for('add_xml', username=username))
            elif datatype == 'postgresql':
                return redirect(url_for('add_postgresql', username=username))
            elif datatype == 'mongodb':
                return redirect(url_for('add_mongodb', username=username))

        if go_to_pipeline.validate_on_submit():
            data_name = go_to_pipeline.data_name.data
            return redirect(url_for('create_pipeline', username=username, data_name=data_name))
        return render_template(
            'data_sources.html',
            go_to_pipeline=go_to_pipeline,
            data_types_form=data_types_form,
            data_sources=(all_users[username].data_sources.values() if username in all_users else [])
        )
    except Exception as exc:
        raise exc
        app.logger.info('Exception: {0}'.format(exc))


@app.route('/create_pipeline', methods=['GET', 'POST'])
def create_pipeline():
    username = request.args.get('username')
    data_name = request.args.get('data_name')
    create_model = CreateModel(username=username, data_name=data_name)
    if create_model.validate_on_submit():
        username = create_model.username.data
        data_name = create_model.username.data
        model_type = create_model.username.data

        if model_type == 'SARIMA':
            return redirect(url_for('show_data', username=username, data_name=data_name, model_type=model_type))

    return render_template(
            'from_form.html',
            form=create_model
    )

@app.route('/dashboard', methods=['GET', 'POST'])
def get_dashboard():
    pass


@app.route('/add_csv', methods=['GET', 'POST'])
def add_csv():
    try:
        username = request.args.get('username')
        csv_form = CSVFileForm(username=username)

        if csv_form.validate_on_submit():
            username = csv_form.username.data
            data_name = csv_form.data_name.data
            file_path = csv_form.file_path.data
            separator = csv_form.separator.data

            all_users[username].data_sources[data_name] = (
                Data(data_name, 'csv', file_path, None, separator=separator)
            )
            return redirect(url_for('show_data', username=username))
        return render_template(
            'from_form.html', form=csv_form
        )
    except Exception as exc:
        raise exc
        app.logger.info('Exception: {0}'.format(exc))

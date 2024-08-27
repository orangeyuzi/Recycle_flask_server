from flask import Flask, render_template, jsonify, request, url_for, redirect, session, Blueprint
from flask_cors import CORS
import secrets
import mariadb
import sys
import os


statistic = Blueprint('statistic', __name__, template_folder='..\\statistic')
CORS(statistic) # 跨平台使用

statistic.secret_key = secrets.token_hex(16) # 保護session

DB_CONFIG = os.getenv(DB_CONFIG)
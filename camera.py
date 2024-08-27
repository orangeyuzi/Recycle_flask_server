from flask import Flask, render_template, jsonify, request, url_for, redirect, session, Blueprint
from flask_cors import CORS
import secrets
import mariadb
import sys
import os
camera = Blueprint('camera', __name__, template_folder='..\\camera')
CORS(camera) # 跨平台使用

camera.secret_key = secrets.token_hex(16) # 保護session
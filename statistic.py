from flask import Flask, render_template, jsonify, request, url_for, redirect, session, Blueprint
from flask_cors import CORS
import json
import secrets
import mariadb
import sys
import os
from datetime import datetime, timedelta

statistic = Blueprint('statistic', __name__, template_folder='..\\statistic')
CORS(statistic) # 跨平台使用

statistic.secret_key = secrets.token_hex(16) # 保護session

# 定義對應字典
type_mapping = {
    "寶特瓶": "塑膠類",
    "便當盒": ["紙類", "一般垃圾"],
    "菸盒": "金屬類"
}

# 資料庫連接設定
DB_CONFIG = {
    "user": "root",
    "password": "mis114",
    "host": "127.0.0.1",
    "port": 3307,
    "database": "recycle",
}

def fetch_pie_data(email):
    try:
        conn = mariadb.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("SELECT UID FROM user WHERE email = %s", (email,))
        user_uids = cursor.fetchall()
        if not user_uids:
            return {"message": "No user found with the given email."}

        user_uid_list = [uid[0] for uid in user_uids]

        format_uid_list = ', '.join(['%s'] * len(user_uid_list))
        query = f"SELECT type FROM camera_data WHERE UID IN ({format_uid_list})"
        cursor.execute(query, user_uid_list)

        results = cursor.fetchall()

        category_count = {}
        for row in results:
            type_ = row[0]
            categories = type_mapping.get(type_, [])
            if not isinstance(categories, list):
                categories = [categories]
            
            for category in categories:
                if category in category_count:
                    category_count[category] += 1
                else:
                    category_count[category] = 1

    except mariadb.Error as err:
        return {"error": str(err)}

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    formatted_data = [{"value": count, "label": label} for label, count in category_count.items()]
    return formatted_data

def fetch_bar_data(email):
    try:
        conn = mariadb.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("SELECT UID FROM user WHERE email = %s", (email,))
        user_uids = cursor.fetchall()
        if not user_uids:
            return {"message": "No user found with the given email."}

        user_uid_list = [uid[0] for uid in user_uids]

        format_uid_list = ', '.join(['%s'] * len(user_uid_list))
        today = datetime.now().date()
        query = f"""
            SELECT type FROM camera_data 
            WHERE UID IN ({format_uid_list})
            AND DATE(Time) = %s
        """
        cursor.execute(query, (*user_uid_list, today))

        results = cursor.fetchall()

        category_count = {}
        for row in results:
            type_ = row[0]
            categories = type_mapping.get(type_, [])
            if not isinstance(categories, list):
                categories = [categories]
            
            for category in categories:
                if category in category_count:
                    category_count[category] += 1
                else:
                    category_count[category] = 1

    except mariadb.Error as err:
        return {"error": str(err)}

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    formatted_data = [{"value": count, "label": label} for label, count in category_count.items()]
    return formatted_data

def fetch_weekly_data(email, category):
    try:
        conn = mariadb.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("SELECT UID FROM user WHERE email = %s", (email,))
        user_uids = cursor.fetchall()
        if not user_uids:
            return {"message": "No user found with the given email."}

        user_uid_list = [uid[0] for uid in user_uids]

        format_uid_list = ', '.join(['%s'] * len(user_uid_list))
        today = datetime.now().date()
        one_week_ago = today - timedelta(days=7)

        query = f"""
            SELECT DATE(Time), COUNT(*) FROM camera_data 
            WHERE UID IN ({format_uid_list})
            AND type = %s
            AND DATE(Time) BETWEEN %s AND %s
            GROUP BY DATE(Time)
        """
        cursor.execute(query, (*user_uid_list, category, one_week_ago, today))

        results = cursor.fetchall()

        week_data = {
            "Mon": 0,
            "Tue": 0,
            "Wed": 0,
            "Thu": 0,
            "Fri": 0,
            "Sat": 0,
            "Sun": 0
        }

        for date_, count in results:
            day_of_week = date_.strftime("%a")
            week_data[day_of_week] = count

    except mariadb.Error as err:
        return {"error": str(err)}

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    formatted_data = [{"value": week_data[day], "label": day} for day in week_data]
    return formatted_data

@app.route('/showAllStatistic', methods=['POST'])
def showAllStatistic():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"error": "Email not provided"}), 400

    result = fetch_pie_data(email)
    return jsonify(result)

@app.route('/showDailyStatistic', methods=['POST'])
def showDailyStatistic():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"error": "Email not provided"}), 400

    result = fetch_bar_data(email)
    return jsonify(result)

@app.route('/showWeeklyStatistic', methods=['POST'])
def showWeeklyStatistic():
    data = request.get_json()
    email = data.get('email')
    category = data.get('category')

    if not email or not category:
        return jsonify({"error": "Email or category not provided"}), 400

    result = fetch_weekly_data(email, category)
    return jsonify(result)
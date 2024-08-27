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

def fetch_and_process_data(email):
    try:
        # 連接到資料庫
        conn = mariadb.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 查找符合 email 的使用者 UID
        cursor.execute("SELECT UID FROM user WHERE email = %s", (email,))
        user_uids = cursor.fetchall()
        if not user_uids:
            return {"message": "No user found with the given email."}

        # 取得所有 UID
        user_uid_list = [uid[0] for uid in user_uids]

        # 查詢 camera_data 資料表中這些 UID 的資料
        format_uid_list = ', '.join(['%s'] * len(user_uid_list))
        query = f"SELECT UID, Time, type FROM camera_data WHERE UID IN ({format_uid_list})"
        cursor.execute(query, user_uid_list)

        # 取得所有結果
        results = cursor.fetchall()

        # 計算每種類別的數量
        category_count = {}
        
        for row in results:
            uid, time, type_ = row
            # 根據 type 對應到不同種類
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
        # 關閉連接
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    # 返回 JSON 格式的結果
    formatted_data = [{"value": count, "label": label} for label, count in category_count.items()]
    return formatted_data

def fetch_weekly_data(email, category):
    try:
        # 連接到資料庫
        conn = mariadb.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 查找符合 email 的使用者 UID
        cursor.execute("SELECT UID FROM user WHERE email = %s", (email,))
        user_uids = cursor.fetchall()
        if not user_uids:
            return {"message": "No user found with the given email."}

        # 取得所有 UID
        user_uid_list = [uid[0] for uid in user_uids]

        # 計算一週前的日期
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        # 查詢過去一週內特定 category 的資料
        format_uid_list = ', '.join(['%s'] * len(user_uid_list))
        query = f"""
            SELECT DATE(Time) AS date, COUNT(*) AS count
            FROM camera_data
            WHERE UID IN ({format_uid_list})
              AND type = %s
              AND Time BETWEEN %s AND %s
            GROUP BY DATE(Time)
        """
        cursor.execute(query, (*user_uid_list, category, start_date, end_date))

        # 取得結果
        results = cursor.fetchall()

        # 初始化每一天的計數
        days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        daily_count = {day: 0 for day in days_of_week}

        # 將結果填充到對應的日期
        for row in results:
            date, count = row
            day_name = date.strftime('%a')
            day_name = {
                'Mon': 'Mon',
                'Tue': 'Tue',
                'Wed': 'Wed',
                'Thu': 'Thu',
                'Fri': 'Fri',
                'Sat': 'Sat',
                'Sun': 'Sun'
            }.get(day_name, 'Unknown')
            if day_name in daily_count:
                daily_count[day_name] += count

    except mariadb.Error as err:
        return {"error": str(err)}

    finally:
        # 關閉連接
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    # 返回 JSON 格式的結果
    formatted_data = [{"value": daily_count[day], "label": day} for day in days_of_week]
    return formatted_data

@app.route('/showPieBarStatistic', methods=['POST'])
def show_pie_bar_statistic():
    # 從請求中獲取 JSON 資料
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"error": "Email not provided"}), 400

    # 處理資料並返回結果
    result = fetch_and_process_data(email)
    return jsonify(result)

@app.route('/weeklyStatistics', methods=['POST'])
def weekly_statistics():
    # 從請求中獲取 JSON 資料
    data = request.get_json()
    email = data.get('email')
    category = data.get('category')

    if not email or not category:
        return jsonify({"error": "Email or category not provided"}), 400

    # 處理資料並返回結果
    result = fetch_weekly_data(email, category)
    return jsonify(result)
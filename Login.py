from flask import Flask, render_template, jsonify, request, url_for, redirect, session, Blueprint
from flask_cors import CORS
import secrets
import mariadb
import sys


# 建立實體
login = Blueprint('login', __name__, template_folder='..\\Login')
CORS(login) # 跨平台使用

login.secret_key = secrets.token_hex(16) # 保護session

# # 資料庫提取資料
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:mis114monkey@localhost:3307/mis114_monkey' 
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db = SQLAlchemy(app) 
# migrate = Migrate(app, db)

# 渲染頁面
@login.route('/')
def index():
    return render_template("index.tsx")

# 登入功能
# 預設照片為no_pic，預設名字為no_name
@login.route('/loginSubmit', methods=["GET", "POST"])
def get_login_data():
    
    if request.method == "POST":
        # 取表單資料
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        # 連接資料庫
        try:
            conn = mariadb.connect(
                user="root", 
                password="mis114monkey", 
                host="127.0.0.1", 
                port=3307, 
                database="mis114_monkey" 
            )
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)
        
        # 讀取資料庫資料
        cur = conn.cursor()
        cur.execute("SELECT Password, Headimg_link, User_name FROM user WHERE Email=? LIMIT 1", (email,))
        rows = cur.fetchall()
        if rows:
            for Password, Headimg_link, User_name  in rows:
                if password == Password:
                    session['img'] = Headimg_link
                    session['name'] = User_name
                    session['state'] = "success"
                else:
                    session['state'] = "wrongPassword" # 不確定為什麼帳號錯也是回傳密碼錯誤，我再看看(已解決)

        else:
            session['state'] = "wrongEmail"

        conn.close()
        return redirect(url_for("login.get_login_data")) # 網頁重新導向，避免重複提交資料

    # 讀取session資料
    img = session.get('img', "profile-user.png")
    name = session.get('name', "no_name")
    state = session.get('state', "wrongEmail")
    session.clear() # 將session裡的資料清除，不清除的話下次測試會直接登入

    return jsonify({"headImg": img, "username": name, "state": state})
    
# 註冊功能
@login.route('/registerSubmit', methods=["GET", "POST"])
def get_register_data():
    
    if request.method == "POST":
        # 取表單資料
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        username = data.get('username')
        # headimg = data.get('username')
        
        # 連接資料庫
        try:
            conn = mariadb.connect(
                user="root", 
                password="mis114monkey", 
                host="127.0.0.1", 
                port=3307, 
                database="mis114_monkey" 
            )
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)
        
        # 讀取資料庫資料
        cur = conn.cursor()
        cur.execute("SELECT Email FROM user WHERE Email=? LIMIT 1", (email,))
        rows = cur.fetchall()
        if rows:
            session['state'] = "wrongEmail"
        else:
            cur.execute("SELECT User_name FROM user WHERE User_name=? LIMIT 1", (username,))
            rows = cur.fetchall()
            if rows:
                session['state'] = "wrongUsername"
            else:
                if password.isalnum():
                    try: 
                        cur.execute("INSERT INTO user (Email, User_name, Password, isCamera, Headimg_link) VALUES (?, ?, ?, ?, ?)", (email, username, password, "N", "profile-user.png"))
                        conn.commit() 
                    except mariadb.Error as e: 
                        print(f"Error: {e}")
                    session['state'] = "success"
                else:
                    session['state'] = "wrongPassword"
        conn.close()

        return redirect(url_for("login.get_register_data")) # 網頁重新導向，避免重複提交資料

    # 讀取session資料
    state = session.get('state', "wrongEmail")
    session.clear() # 將session裡的資料清除，不清除的話下次測試會直接登入
    
    return jsonify({"state": state, "headImg": "profile-user.png"})
# 執行程式
if __name__ == '__main__':
    login.run(host="0.0.0.0", port=5000) # 我先設這個，有更好的話可以直接提出來討論修改

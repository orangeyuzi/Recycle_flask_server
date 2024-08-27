from flask import Flask
from flask_cors import CORS
from login import login
from statistic import statistic
from camera import camera
import secrets


app = Flask(__name__)
CORS(app)  # 跨平台使用

app.secret_key = secrets.token_hex(16)  # 保護session



# 註冊附屬檔案在APP上
app.register_blueprint(login)  # 登入介面後端
app.register_blueprint(modify) # modify
app.register_blueprint(statistic)  # 統計後端
app.register_blueprint(camera) #相機後端

# 執行程式
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)  # 我先設這個，有更好的話可以直接提出來討論修改

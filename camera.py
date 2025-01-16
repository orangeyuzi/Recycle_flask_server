# 伺服器所需的套件
from flask import Flask, render_template, jsonify, request, url_for, redirect, session, Blueprint
from flask_cors import CORS
import secrets
import mariadb
import sys
# 銜接模型的套件
from tensorflow.lite.python.interpreter import Interpreter
import cv2
import numpy as np
import pandas as pd
# 資料庫所需資料的套件
from datetime import datetime
from werkzeug.utils import secure_filename
from pypinyin import lazy_pinyin
import json

camera = Blueprint('camera', __name__, template_folder='..\\camera')
CORS(camera) # 跨平台使用

camera.secret_key = secrets.token_hex(16) # 保護session

# 所有路徑
PATH_TO_MODEL = './detect.tflite' # 這裡放模型的連結
PATH_TO_LABELS='./labelmap.txt' # 這邊放分種類的檔案的連結，預計會有(類別 建議\n類別 建議)

# 從input details 去改 width 和 height
width = 640
height = 640

def tflite_detect_image(interpreter, image, labels, min_conf=0.6):
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    # print(input_details)

    imH, imW, _ = image.shape
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_resized = cv2.resize(image_rgb, (width, height))
    input_data = np.expand_dims(image_resized, axis=0)

    float_input = (input_details[0]['dtype'] == np.float32)

    if float_input:
        input_data = (np.float32(input_data) - 127.5) / 127.5

    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()

    # boxes = interpreter.get_tensor(output_details[1]['index'])[0]
    classes = interpreter.get_tensor(output_details[3]['index'])[0]
    scores = interpreter.get_tensor(output_details[0]['index'])[0]

    detections = []
    # label_count = {}
    best_score = 0

    for i in range(len(scores)):
        if scores[i] > best_score and scores[i] > min_conf and scores[i] <= 1.0:

            best_score = scores[i]

            # ymin = int(max(1, (boxes[i][0] * imH)))
            # xmin = int(max(1, (boxes[i][1] * imW)))
            # ymax = int(min(imH, (boxes[i][2] * imH)))
            # xmax = int(min(imW, (boxes[i][3] * imW)))

            # cv2.rectangle(image, (xmin, ymin), (xmax, ymax), (10, 255, 0), 2)

            object_name = labels[int(classes[i])]

            #  label count
            # if object_name in label_count:
            #     label_count[object_name] += 1
            # else:
            #     label_count[object_name] = 1

            # label = '%s-%d : %d%%' % (object_name, label_count.get(object_name, 0), int(scores[i] * 100))
            # labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            # label_ymin = max(ymin, labelSize[1] + 10)
            # cv2.rectangle(image, (xmin, label_ymin - labelSize[1] - 10), (xmin + labelSize[0], label_ymin + baseLine - 10), (255, 255, 255), cv2.FILLED)
            # cv2.putText(image, label, (xmin, label_ymin - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

            detections.append([object_name, scores[i]])
            best_detection = object_name

    return image, detections, best_detection

@camera.route('/sendRcycle', methods=["GET", "POST"])
def get_recycle_model_result():
    if request.method == "POST":
        # 取表單資料
        image = request.files['image']
        email = request.form['email']
        image_name = image.filename
        image_name = secure_filename(''.join(lazy_pinyin(image_name)))
        image.save(f'static/recycleImg/{image_name}')
        img_path = "static/recycleImg/" + image_name

        interpreter = Interpreter(model_path=PATH_TO_MODEL)
        interpreter.allocate_tensors()

        with open(PATH_TO_LABELS, 'r') as f:
            labels = [line.split()[0] for line in f.readlines()]

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

        with open(PATH_TO_LABELS, 'r') as f:
            label_dict = {line.split()[0]: ' '.join(line.split()[1:]) for line in f.readlines()}

        # 獲取模型結果
        processed_frame, detections, best_detection = tflite_detect_image(interpreter, image, labels, min_conf=0.6)
        current_time = datetime.now()

        # 讀取資料庫資料
        cur = conn.cursor()
        cur.execute(
            "SELECT UID FROM user WHERE Email=? LIMIT 1", (email,))
        rows = cur.fetchall()
        if rows:
            cur.execute("INSERT INTO camera_data (UID, Time, Type, Pic_Address) VALUES (?, ?, ?, ?)", (rows[0], current_time, best_detection, img_path))

            conn.commit()
            session['title'] = best_detection
            session['paragraph'] = label_dict[best_detection]
            conn.close()

            return redirect(url_for("camera.get_recycle_model_result"))  # 網頁重新導向，避免重複提交資料
    # 讀取session資料
    title = session.get('title', "No Result!")
    paragraph = session.get('paragraph', "There is something wrong!")
    session.clear()  # 將session裡的資料清除

    return jsonify({"title": title, "paragraph": paragraph})
    



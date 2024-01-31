import ultralytics
import torch
import torchvision
from ultralytics import YOLO

import os
import cv2
from ultralytics.utils.plotting import Annotator
import numpy as np
import time
from PIL import Image
import glob
import json



data_list = []
image_list = []
class_list = [0]*9
sum_defect = 0
model_path = os.path.join('best.pt')
VIDEOS_DIR = os.path.join('.', 'videos')
IMG_DIR = os.path.join('.', 'img')

img_path = os.path.join('006783.jpg')
model = YOLO(model_path)
cap = cv2.VideoCapture(img_path)


start = False
while True:
    ret, img = cap.read()
    
    if not ret: 
        break
    
    results = model.predict(img)

    for r in results:
        annotator = Annotator(img,font_size=0.1)
        
        boxes = r.boxes
        for box in boxes:
            # print(f"boxSSSS: {box}")
            # print(f"resultsType: {type(box)}")
            # box คือ แต่ละ กรอบ ที่มันจับได้ ใน boxes(ใหญ่)
            b = box.xyxy[0]  # get box coordinates in (top, left, bottom, right) format
            Top = int(b[0])
            Left = int(b[1])
            Bottom = int(b[2])
            Right = int(b[3])
            h = Right - Left  # wide
            w = Bottom - Top  # high
            
            d = box.xywh[0]
            Toph = float(d[0])
            Lefth = float(d[1])
            Weighth = float(d[2])
            Heighth = float(d[3])

            f = box.xywhn[0]
            Xn = float(f[0])
            Yn = float(f[1])
            Weighthn = float(f[2])
            Heighthn = float(f[3])

            g = box.cls[0]
            clazz = int(g)

            c = box.cls
            #annotator.box_label(b)

            class_list[clazz] = class_list[clazz] + 1
            
            sum_defect+=1

            annotator.box_label(b, model.names[int(c)])
            
            
            #defect dict
            dictionary = {
                 "Class": clazz,
                 "X": Xn,
                 "Y": Yn,
                 "W": Weighthn,
                 "H": Heighthn
            }

            data_list.append(dictionary)

    defect_sum = {
        "AllDefect" : sum_defect,
        "0" : class_list[0],
        "1" : class_list[1],
        "2" : class_list[2],
        "3" : class_list[3],
        "4" : class_list[4],
        "5" : class_list[5],
        "6" : class_list[6],
        "7" : class_list[7],
        "8" : class_list[8]
    }
    data_list.append(defect_sum)

    with open('number.json', 'w') as out_file:
        json.dump(data_list,out_file, indent=9)

    img = annotator.result()

    data_list.clear()

cap.release()

cv2.destroyAllWindows()



from fastapi import APIRouter
from models.modl import User,Factory,Building,Image,Defect,DefectLocation,Permission
from config.database import collection_user,collection_building,collection_factory,collection_Image,collection_DefectLocation,collection_Defect,collection_Permission
from schema.schemas import list_serial_user,list_serial_build,list_serial_factory,list_serial_image,list_serial_defectlo,list_serial_defec,list_serial_permis
from bson import ObjectId

import ultralytics
import torch
import torchvision
from ultralytics import YOLO
import os
import cv2
from ultralytics.utils.plotting import Annotator
import numpy as np
import time
import json

router = APIRouter()

#-----User-----
#GET Request Method
@router.get("/Get User")
async def get_usr_lis() :
    usr_lis = list_serial_user(collection_user.find())
    return usr_lis

#POST Request Method
@router.post("/Post User")
async def post_usr_lis(usr: User):
    collection_user.insert_one(dict(usr))


#-----Factory-----
# GET Request Method
@router.get("/Get Factory")
async def get_facto_lis() :
    facto_lis = list_serial_factory(collection_factory.find())
    return facto_lis

#POST Request Method
@router.post("/Post Factory")
async def post_facto_lis(facto: Factory):
    collection_factory.insert_one(dict(facto))


#-----Building-----
#Find Factory Name
factory_unique = {"factory_name" : "ThaiBev"}
find_factory = collection_factory.find(factory_unique)

for each_doc in find_factory:
    factory_id = each_doc['_id']

# GET Request Method
@router.get("/Get Building")
async def get_build_lis() :
    build_lis = list_serial_build(collection_building.find())
    return build_lis

#POST Request Method
@router.post("/Post Building")
async def post_build_lis(build: Building):
    build_doc = dict(build)
    build_doc['factory_id'] = factory_id
    collection_building.insert_one(build_doc)


#-----Image-----
building_unique = {"data_location" : "/Program/Data/BuildingA"}
find_image = collection_building.find(building_unique)

for each_doc in find_image:
    building_id = each_doc['_id']

# GET Request Method
@router.get("/Get Image")
async def get_image_lis() :
    img_lis = list_serial_image(collection_Image.find())
    return img_lis

#POST Request Method
@router.post("/Post Image")
async def post_image_lis(img: Image):
    image_doc = dict(img)
    image_doc['building_id'] = building_id
    collection_Image.insert_one(image_doc)


#-----DefectLocation-----
image_unique = {"image_path" : "/Program/Data/BuildingA/img0001.jpg"}
find_image = collection_Image.find(image_unique)

#get position's image path and model path
img_path = os.path.join('006783.jpg')
model_path = os.path.join('best.pt')
model = YOLO(model_path)
cap = cv2.VideoCapture(img_path)

for each_doc in find_image:
    image_id = each_doc['_id']

# GET Request Method by image_id
@router.get("/Get DefectLocation")
async def get_defectlo_lis() :
    defectlo_lis = list_serial_defectlo(collection_DefectLocation.find())
    return defectlo_lis

#POST Request Method
@router.post("/Post DefectLocation")
async def post_defectlo_lis(defectlo: DefectLocation):
    while True:
        ret, img = cap.read()
    
        if not ret: 
            break
    
        results = model.predict(img)

        for r in results:
            annotator = Annotator(img,font_size=0.1)
        
            boxes = r.boxes
            for box in boxes:
                f = box.xywhn[0]
                Xn = float(f[0])
                Yn = float(f[1])
                Weighthn = float(f[2])
                Heighthn = float(f[3])

                g = box.cls[0]
                clazz = int(g)
            
                #defect dict
                predict_defect_dict = {
                     "Class": clazz,
                     "X": Xn,
                     "Y": Yn,
                     "W": Weighthn,
                     "H": Heighthn
                }

                #defectlocation open dict
                defectlocation_doc = dict(defectlo)
                defectlocation_doc['class_type'] = predict_defect_dict['Class']
                defectlocation_doc['x'] = predict_defect_dict['X']
                defectlocation_doc['y'] = predict_defect_dict['Y']
                defectlocation_doc['w'] = predict_defect_dict['W']
                defectlocation_doc['h'] = predict_defect_dict['H']
                defectlocation_doc['image_id'] = image_id
                class_type = defectlocation_doc['class_type']
                class_data = collection_Defect.find({"defect_class" : class_type})
                for each_doc in class_data:
                    class_name = each_doc['defect_class_name']
                defectlocation_doc['class_name'] = class_name
                collection_DefectLocation.insert_one(defectlocation_doc)
                defectlocation_doc.clear()
        img = annotator.result()

    cap.release()
    cv2.destroyAllWindows()


#-----Permission-----
factory_unique = {"factory_name" : "ThaiBev"}
find_factory = collection_factory.find(factory_unique)

for each_doc in find_factory:
    factory_id = each_doc['_id']

user_unique = {"username" : "Admin"}
find_user = collection_user.find(user_unique)

for each_doc in find_user:
    user_id = each_doc['_id']
    print(user_id)

#GET Request Method
@router.get("/Get Permission")
async def get_permis_lis() :
    permis_lis = list_serial_permis(collection_Permission.find())
    return permis_lis

#Post Request Method
@router.post("/Post Permission")
async def post_permis_lis(permis: Permission):
    permis_doc = dict(permis)
    permis_doc['user_id'] = user_id
    permis_doc['factory_id'] = factory_id
    collection_Permission.insert_one(permis_doc)

#-----Defect-----
# GET Request Method
@router.get("/Get Defect")
async def get_defec_lis() :
    defec_lis = list_serial_defec(collection_Defect.find())
    return defec_lis

#POST Request Method
@router.post("/Post Defect")
async def post_defec_lis(defec: Defect):
    defect_doc = dict(defec)
    collection_Defect.insert_one(_doc)

# @router.put("/{id}")
# async def put_todo(id: str, todo: Todo):
#     collection_name.find_one_and_update({"_id": ObjectId(id)}, {"$set": dict(todo)})

# @router.delete("/{id}")
# async def delete_todo(id:str):
#     collection_name.find_one_and_delete({"_id": ObjectId(id)})
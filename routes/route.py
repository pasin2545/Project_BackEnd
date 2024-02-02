from fastapi import APIRouter
from models.modl import User,Factory,Building,Image,Defect,DefectLocation,Permission
from config.database import collection_user,collection_building,collection_factory,collection_Image,collection_DefectLocation,collection_Defect,collection_Permission
from schema.schemas import list_serial_user,list_serial_build,list_serial_factory,list_serial_image,list_serial_defectlo,list_serial_defec,list_serial_permis
from bson import ObjectId
from typing import List

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

# GET Request Method for image when need to show image which have defect
@router.get("/Get Image")
async def get_image_lis(building_data_location : str) :
    image_path_list = []

    building_data = {"data_location" : building_data_location}
    which_building = collection_building.find(building_data)
    for just_one_building in which_building:
        which_building_id = just_one_building['_id']

        find_image_by_building_id = {'building_id' : ObjectId(which_building_id)}
        which_image = collection_Image.find(find_image_by_building_id)
        for each_image in which_image:
            defect_count = 0 
            which_image_id = each_image['_id']
            find_defectlo_by_image_id = {'image_id' : ObjectId(which_image_id)}
            have_defect = (collection_DefectLocation.find(find_defectlo_by_image_id))
            defect_count = have_defect.count()
            if defect_count > 0 :
                which_image_path = each_image['image_path']
                image_path_list.append({"image_path": which_image_path})

    return image_path_list

#POST Request Method
@router.post("/Post Image")
async def post_image_lis(img: Image):
    image_doc = dict(img)
    image_doc['building_id'] = building_id
    collection_Image.insert_one(image_doc)


#-----DefectLocation-----
# GET Request Method by image_id
@router.get("/Get DefectLocation")
async def get_defectlo_lis(image_path_for_defect : str) :
    
    defectlo_lis = list_serial_defectlo(collection_DefectLocation.find())
    return defectlo_lis

#POST Request Method for redefine the defect square
@router.post("/Post DefectLocation for Redefine")
async def post_defectlo_lis_redefine(defectlos: List[DefectLocation]):
    image_unique = {"image_path" : "/Program/Data/BuildingA/img0001.jpg"}
    find_image = collection_Image.find(image_unique)

    for each_doc in find_image:
        image_id = each_doc['_id']

    for defectlo in defectlos:
        defectlocation_doc = dict(defectlo)
        defectlocation_doc['image_id'] = image_id
        class_type = defectlocation_doc['class_type']
        class_data = collection_Defect.find({"defect_class" : class_type})
        for each_doc in class_data:
            class_name = each_doc['defect_class_name']
        defectlocation_doc['class_name'] = class_name
        collection_DefectLocation.insert_one(defectlocation_doc)
        defectlocation_doc.clear()


#POST Request Method for use model detection
image_unique = {"image_path" : "/Program/Data/BuildingA/img0003.jpg"}
#Use image path for parameter
@router.post("/Post DefectLocation for Model")
async def post_defectlo_lis_model():

    #get position's image path and model path
    img_path = os.path.join('000001.jpg')
    model_path = os.path.join('best.pt')
    model = YOLO(model_path)
    cap = cv2.VideoCapture(img_path)

    find_image = collection_Image.find(image_unique)

    for each_doc in find_image:
        image_id = each_doc['_id']

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
            
                defect_location = DefectLocation(class_type=clazz, x=Xn, y=Yn, w=Weighthn, h=Heighthn)

                # Convert DefectLocation instance to dictionary
                defectlocation_doc = defect_location.dict()

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

# Delete Request Method
@router.delete("/{image_id}")
async def delete_defectlo_lis(image_id: str):
    defectloc_image = collection_DefectLocation.find({"image_id": ObjectId(image_id)})
    
    for each_doc in defectloc_image:
        defectlo_id = each_doc['_id']
        collection_DefectLocation.find_one_and_delete({"_id": defectlo_id})
    
    
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
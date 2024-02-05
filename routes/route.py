from fastapi import APIRouter
from models.modl import User,Factory,Building,Image,Defect,DefectLocation,Permission
from config.database import collection_user,collection_building,collection_factory,collection_Image,collection_DefectLocation,collection_Defect,collection_Permission
from schema.schemas import list_serial_user,list_serial_build,list_serial_factory,list_serial_image,list_serial_defectlo,list_serial_defec,list_serial_permis
from bson import ObjectId
from typing import List
import asyncio
from fastapi import HTTPException

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

#-------------------------------------------------------User-------------------------------------------------------
#GET Request Method for verified user
@router.get("/Get User Verified")
async def get_usr_verified() :
    usr_lis = list_serial_user(collection_user.find({'is_verified' : True}))
    return usr_lis

#GET Request Method for unverified user
@router.get("/Get User Unverified")
async def get_usr_unverified() :
    usr_lis = list_serial_user(collection_user.find({'is_verified' : False}))
    return usr_lis

#POST Request Method
@router.post("/Post User")
async def post_usr_lis(usr: User):
    collection_user.insert_one(dict(usr))

#PUT Request Method for verified user
@router.put("/put_verified")
async def put_user_verified(verified : bool,username_veri : str):
    who_user = collection_user.find_one({'username' : username_veri})

    if who_user:
        collection_user.update_one({'username' : username_veri}, {'$set': {'is_verified' : verified}})
    else:
        raise HTTPException(status_code=404, detail=f"User '{username_veri}' not found.")

#PUT Request Method for change password
@router.put("/put_change_password")
async def put_user_password(password : str, username_change : str):
    who_user = collection_user.find_one({'username' : username_change})

    if who_user:
        collection_user.update_one({'username' : username_change},{'$set': {'password' : password}})
    else:
        raise HTTPException(status_code=404, detail=f"User '{username_veri}' not found.")

# Delete User Method
@router.delete("/user/{username}")
async def delete_user(username_delete : str) :
    await delete_user_permis(str(username_delete))
    collection_user.find_one_and_delete({'username' : username_delete})


#-------------------------------------------------------Factory-------------------------------------------------------
# GET Request Method for admin look factory
@router.get("/Get Admin Factory")
async def get_facto_lis() :
    facto_lis = list_serial_factory(collection_factory.find())
    return facto_lis

#GET Request Method for user
@router.get("/Get User Factory")
async def get_usr_facto_lis(username : str) :
    facto_lis = []

    who_user = collection_user.find_one({'username' : username})
    who_user_id = who_user['_id']

    which_permis = collection_Permission.find({'user_id' : ObjectId(who_user_id)})

    for each_permis in which_permis:

        each_permis_factory_id = each_permis['factory_id']
        find_factory = collection_factory.find_one({'_id': ObjectId(each_permis_factory_id)})
        find_factory['_id'] = str(find_factory['_id'])
        facto_lis.append(find_factory)

    return facto_lis

#POST Request Method
@router.post("/Post Factory")
async def post_facto_lis(facto: Factory):
    collection_factory.insert_one(dict(facto))

#Delete Factory and delete every thing about it.
@router.delete("/factory/{factory_name_and_detail}")
async def delete_facto(factory_delete_name : str, factory_delete_details : str):
    which_factory = {'$and' : [{'factory_name' : factory_delete_name},{'factory_details' : factory_delete_details}]}
    find_factory_by_name = collection_factory.find(which_factory)

    for that_factory in find_factory_by_name:
        which_factory_id = that_factory['_id']

    find_building_by_facto_id = collection_building.find({'factory_id' : ObjectId(which_factory_id)})

    for that_building in find_building_by_facto_id:
        which_building_path = that_building['data_location']
        await delete_building(str(which_building_path))
    
    await delete_factory_permis(str(factory_delete_name))
    collection_factory.find_one_and_delete({"_id": ObjectId(which_factory_id)})
    

#-------------------------------------------------------Building--------------------------------------------------------
# GET Request Method for user
@router.get("/Get Building")
async def get_build_lis() :
    build_lis = list_serial_build(collection_building.find())
    return build_lis

#POST Request Method
@router.post("/Post Building")
async def post_build_lis(build: Building):
    build_doc = dict(build)
    factory_post_name = build_doc['factory_name']
    factory_post_details = build_doc['factory_details']
    which_factory = {'$and' : [{'factory_name' : factory_post_name},{'factory_details' : factory_post_details}]}
    find_factory = collection_factory.find_one(which_factory)

    which_factory_id = find_factory['_id']

    build_doc['factory_id'] = which_factory_id #factory_id
    build_doc.pop('factory_name' , None)
    build_doc.pop('factory_details' , None)
    collection_building.insert_one(build_doc)

#Delete Building and all about it
@router.delete("/building/{building_path}")
async def delete_building(building_delete_path : str):
    which_building_path = {'data_location' : building_delete_path}
    which_building = collection_building.find(which_building_path)
    print(which_building)

    for that_building in which_building:
        which_building_id = that_building['_id']
    
    find_image_by_building_id = collection_Image.find({'building_id' : ObjectId(which_building_id)})

    for each_image in find_image_by_building_id :
        each_image_path = each_image['image_path']
        await delete_image_lis(str(each_image_path))
    
    collection_building.find_one_and_delete({'_id' : ObjectId(which_building_id)})

#-------------------------------------------------------Image-------------------------------------------------------

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
    building_post_path = image_doc['building_path']
    find_building = collection_building.find({'data_location' : building_post_path})

    for each_building in find_building:
        which_building_id = each_building['_id']

    image_doc['building_id'] = which_building_id #building_id
    image_doc.pop('building_path' , None)
    collection_Image.insert_one(image_doc)

# Delete Request Method for image
@router.delete("/image/{image_path}")
async def delete_image_lis(image_path_delete : str):
    find_image_by_image_path = {'image_path' : image_path_delete}
    which_image = collection_Image.find(find_image_by_image_path)


    tasks = []
    for that_image in which_image:
        which_image_id = that_image['_id']
        print(which_image_id)
        tasks.append(delete_defectlo_lis(str(which_image_id)))
    
    await asyncio.gather(*tasks)

    collection_Image.find_one_and_delete({'_id' : which_image_id})


#-------------------------------------------------------DefectLocation-------------------------------------------------------
# GET Request Method by image_path
@router.get("/Get DefectLocation")
async def get_defectlo_lis(image_path_for_defect : str) :
    image_path = {'image_path' : image_path_for_defect}
    which_image = collection_Image.find(image_path)

    for just_one_image in which_image:
        which_image_id = just_one_image['_id']

    image_id_in_defect = {'image_id' : which_image_id}
    defectlo_lis = list_serial_defectlo(collection_DefectLocation.find(image_id_in_defect))
    return defectlo_lis

#POST Request Method for redefine the defect square
@router.post("/Post DefectLocation for Redefine")
async def post_defectlo_lis_redefine(defectlos: List[DefectLocation], image_post_path : str):
    image_unique = {"image_path" : image_post_path}
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
#Use image path for parameter
@router.post("/Post DefectLocation for Model")
async def post_defectlo_lis_model(image_model_path : str):

    #get position's image path and model path
    img_path = os.path.join(image_model_path) #image path for model
    model_path = os.path.join('best.pt')
    model = YOLO(model_path)
    cap = cv2.VideoCapture(img_path)

    find_image = collection_Image.find(image_model_path)

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

                defectlocation_doc['image_id'] = image_id #image_id
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

# Delete Request Method for redefind defect by image_id
@router.delete("/defectlo/{image_id}")
async def delete_defectlo_lis(image_id: str):
    defectloc_image = collection_DefectLocation.find({"image_id": ObjectId(image_id)})
    
    for each_doc in defectloc_image:
        defectlo_id = each_doc['_id']
        collection_DefectLocation.find_one_and_delete({"_id": defectlo_id})
    
    
#-------------------------------------------------------Permission-------------------------------------------------------
#GET Request Method
@router.get("/Get Permission")
async def get_permis_lis() :
    permis_lis = list_serial_permis(collection_Permission.find())
    return permis_lis

#Post Request Method
@router.post("/Post Permission")
async def post_permis_lis(permis: Permission):
    permis_doc = dict(permis)
    user_post_name = permis_doc['username']
    factory_post_name = permis_doc['factory_name']
    factory_post_details = permis_doc['factory_details']

    find_user = collection_user.find_one({'username' : user_post_name})
    that_user_id = find_user['_id']

    which_factory = {'$and' : [{'factory_name' : factory_post_name},{'factory_details' : factory_post_details}]}
    find_factory = collection_factory.find_one(which_factory)
    that_factory_id = find_factory['_id']

    permis_doc['user_id'] = that_user_id #user_id
    permis_doc['factory_id'] = that_factory_id #factory_id
    permis_doc.pop('username' , None)
    permis_doc.pop('factory_name' , None)
    permis_doc.pop('factory_details' , None)
    collection_Permission.insert_one(permis_doc)

#Delete Permission Method by user
@router.delete("/permis_user/{permis_username}")
async def delete_user_permis(permis_username : str):
    print('delete_user_permis' + ' : ' + permis_username)
    who_user_username = {'username' : str(permis_username)}
    who_user = collection_user.find(who_user_username)

    for that_user in who_user :
        who_user_id = that_user['_id']
        which_permis = collection_Permission.find({'user_id' : ObjectId(who_user_id)})
        for each_permis in which_permis:
            collection_Permission.find_one_and_delete(each_permis)

@router.delete("/permis_facto/{permis_factory}")
async def delete_factory_permis(facto_name : str):
    which_facto_name = {'factory_name' : str(facto_name)}
    which_facto = collection_factory.find(which_facto_name)

    for that_facto in which_facto:
        which_facto_id = that_facto['_id']
        which_permis = collection_Permission.find({'factory_id' : ObjectId(which_facto_id)})
        for each_permis in which_permis:
            collection_Permission.find_one_and_delete(each_permis)


#-------------------------------------------------------Defect-------------------------------------------------------
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
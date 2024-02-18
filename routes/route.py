#coding: utf-8
from fastapi import APIRouter, Depends, HTTPException, Request, File, UploadFile
from models.model import User,Factory,Building,Image,Defect,DefectLocation,Permission, Token, TokenData, CreateUserRequest, ExtractVideo, VerifiedUser, UserChangePassword, ChangeRole, AdminChangePassword, UsernameInput, FactoryId, BuildingId, BuildingPath, ImagePath, ImageId, DefectLocationWithImage, BuildingDetail,CreateAdminRequest, History, HistoryId
from config.database import collection_user,collection_building,collection_factory,collection_Image,collection_DefectLocation,collection_Defect,collection_Permission, collection_history
from schema.schemas import list_serial_user,list_serial_build,list_serial_factory,list_serial_image,list_serial_defectlo,list_serial_defec,list_serial_permis, list_serial_histo
from datetime import datetime
import pytz
from bson import ObjectId
from typing import List, Annotated, Optional
import asyncio
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import timedelta, datetime
from pydantic import BaseModel
from starlette import status
from config.database import db
import shutil
import uuid
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
import glob

router = APIRouter()

SECRET_KEY = 'Roof_Surface'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

#-------------------------------------------------------Auth-------------------------------------------------------

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_user(user: User):
    hashed_password = pwd_context.hash(user.password)
    user.password = hashed_password
    collection_user.insert_one(user.dict())

def get_user(username: str):
    user_data = collection_user.find_one({"username": username})
    if user_data:
        return User(**user_data)

def authenticate_user(username: str, password: str):
    user = get_user(username)
    user_verified = collection_user.find_one({'username' : username})
    if not user or not verify_password(password, user.password):
        return False
    if user_verified['is_verified'] == False :
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else: 
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username = token_data.username)
    if user is None:
        raise credentials_exception
    return user

@router.post("/upload_user_file")
async def upload_file(file:UploadFile):
    file_path = str(uuid.uuid4())
    os.makedirs(f"data/user_file_verified/{file_path}", exist_ok=True)
    file_dir = f"data/user_file_verified/{file_path}/{file.filename}"
    try :
        contents = await file.read()
        with open(file_dir,"wb") as f:
            f.write(contents)
    except Exception:
        return {"message": "There was an error uploading the file"}
    finally:
        await file.close()

    return {"path": file_dir}

@router.post("/sign_up", status_code=status.HTTP_201_CREATED)
async def sign_up(create_user_request: CreateUserRequest):

    create_user_model = User(
        firstname=create_user_request.firstname,
        surname=create_user_request.surname,
        email=create_user_request.email,
        username=create_user_request.username,
        password=create_user_request.password,
        user_verification_file_path=create_user_request.verified_file_path
    )
    create_user(create_user_model)
    return {"message": "User created successfully"}

@router.post("/create_admin", status_code=status.HTTP_201_CREATED)
async def create_admin(create_admin_request: CreateAdminRequest):

    create_admin_model = User(
        firstname=create_admin_request.firstname,
        surname=create_admin_request.surname,
        email=create_admin_request.email,
        username=create_admin_request.username,
        password=create_admin_request.password,
        is_admin=True,
        is_verified=True,
        user_verification_file_path=create_admin_request.verified_file_path
    )
    create_user(create_admin_model)
    return {"message": "User created successfully"}
    
@router.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The identity has not been verified or Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return Token(access_token =  access_token, token_type = "bearer")

@router.get("/users/me/", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):

    return current_user
#-------------------------------------------------------User-------------------------------------------------------

#GET Request Method for verified user
@router.get("/get_user_verified")
async def get_usr_verified() :
    usr_lis = list_serial_user(collection_user.find({'is_verified' : True}))
    return usr_lis

#GET Request Method for unverified user
@router.get("/get_user_unverified")
async def get_usr_unverified() :
    usr_lis = list_serial_user(collection_user.find({'is_verified' : False}))
    return usr_lis

@router.get("/get_admin")
async def get_admin():
    usr_list = list_serial_user(collection_user.find({"is_admin" : True, "is_verified" : True}))
    return usr_list 

#PUT Request Method for verified user
@router.put("/put_verified")
async def put_user_verified(verified : VerifiedUser):
    who_user = collection_user.find_one({'username' : verified.username})

    if who_user:
        collection_user.update_one({'username' : verified.username}, {'$set': {'is_verified' : verified.verified}})
    else:
        raise HTTPException(status_code=404, detail=f"User '{username_veri}' not found.")

#PUT Request Method for change password
@router.put("/put_change_password")
async def put_user_password(userchange : UserChangePassword):
    who_user = collection_user.find_one({'username' : userchange.username})
    
    if who_user:
        if verify_password(userchange.old_password, who_user['password']):
            hashed_password = pwd_context.hash(userchange.new_password)
            collection_user.update_one({'username' : userchange.username},{'$set': {'password' : hashed_password}})
            return {"message": "Password updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Old password is incorrect")
    else:
        raise HTTPException(status_code=404, detail=f"User '{username_veri}' not found.")

@router.put("/admin_change_password")
async def put_admin_password(adminchange : AdminChangePassword):
    who_user = collection_user.find_one({'username' : adminchange.username})

    if who_user:
        hashed_password = pwd_context.hash(adminchange.new_password)
        collection_user.update_one({'username' : adminchange.username},{'$set': {'password' : hashed_password}})
    else:
        raise HTTPException(status_code=404, detail=f"User '{username_veri}' not found.")

# Delete User Method
@router.delete("/user/{username}")
async def delete_user(user_name : UsernameInput) :
    await delete_user_permis(UsernameInput(username = str(user_name.username)))
    collection_user.find_one_and_delete({'username' : user_name.username})


#-------------------------------------------------------Factory-------------------------------------------------------

# GET Request Method for factory information
@router.get("/get_factory_info")
async def get_facto_info(facto_id : str):
    facto_info = collection_factory.find_one({'_id': ObjectId(facto_id)})
    if facto_info:
        facto_info['_id'] = str(facto_info['_id'])
        return facto_info

# GET Request Method for admin look factory in add factory page
@router.get("/get_admin_factory")
async def get_admin_add_permis() :
    facto_lis = list_serial_factory(collection_factory.find({'is_disable' : False}))
    return facto_lis

# GET Request Method for admin factory manage page
@router.get("/get_admin_manage_factory")
async def get_admin_manage():
    facto_lis = list_serial_factory(collection_factory.find())
    return facto_lis

#GET Request Method for show factory to user
@router.get("/get_user_factory")
async def get_usr_facto_lis(username : str) :
    factories_list = []
    

    who_user = collection_user.find_one({'username' : username})
    who_user_id = who_user['_id']

    which_permis = collection_Permission.find({'user_id' : ObjectId(who_user_id)})

    for each_permis in which_permis:
        
        each_permis_factory_id = str(each_permis['factory_id'])
        find_factory = collection_factory.find_one({'_id': ObjectId(each_permis_factory_id)})
        factory_name = find_factory['factory_name']
        factory_status = find_factory['is_disable']
        buildings_lis = []

        if factory_status == False:
            find_building = collection_building.find({'factory_id' : each_permis_factory_id})
            for each_building in find_building:
                building_name = each_building['building_name']
                building_id = str(each_building['_id'])
                buildings_lis.append({
                    'building_name': building_name,
                    'building_id': building_id
                })
            factories_list.append({
                "factory_name": factory_name,
                "factory_id" : each_permis_factory_id,
                "buildings": buildings_lis
            })

    return factories_list

#Get Method for admin permission summary
@router.get("/permission_summary")
async def get_permission_summary():
    factory_list = []
    all_factory = collection_factory.find()

    for each_factory in all_factory:
        each_factory_name = str(each_factory["factory_name"])
        each_factory_id = each_factory["_id"]

        user_list = []
        user_count = 0

        find_permission = collection_Permission.find({"factory_id" : each_factory_id})
        for each_permission in find_permission:
            user_count += 1
            user_permis_id = each_permission["user_id"]
            find_user = collection_user.find_one({"_id" : ObjectId(user_permis_id)})
            user_name = find_user['username']
            user_list.append({"username" : user_name})

        factory_list.append({"factory_name" : each_factory_name, 
        "user_count" : user_count, 
        "user_permis" : user_list
        })
    
    return factory_list     

#PUT Method for admin change between factory (disable=Ture) and (enable=False)
@router.put("/put_change_facto_status")
async def put_change_facto_status(id_facto : FactoryId):

    find_factory = collection_factory.find_one({'_id' : ObjectId(id_facto.facto_id)})

    if find_factory :
        
        if find_factory['is_disable'] == True:
            collection_factory.update_one({'_id' : ObjectId(id_facto.facto_id)},{'$set': {'is_disable' : False}})
        elif find_factory['is_disable'] == False:
            collection_factory.update_one({'_id' : ObjectId(id_facto.facto_id)},{'$set': {'is_disable' : True}})

#POST Request Method
@router.post("/post_factory")
async def post_facto_lis(facto: Factory):
    collection_factory.insert_one(dict(facto))

#Delete Factory and delete every thing about it.
@router.delete("/factory/{factory_name_and_detail}")
async def delete_facto(id_facto : FactoryId):

    find_building_by_facto_id = collection_building.find({'factory_id' : str(id_facto.facto_id)})

    for that_building in find_building_by_facto_id:
        which_building_id = that_building['_id']
        await delete_building(BuildingId(build_id = str(which_building_id)))
    
    await delete_factory_permis(FactoryId(facto_id = str(id_facto.facto_id)))
    collection_factory.find_one_and_delete({"_id": ObjectId(id_facto.facto_id)})
    
#-------------------------------------------------------Building--------------------------------------------------------

# GET Request Method for factory information
@router.get("/get_building_info")
async def get_build_info(build_id : str):
    obj_id = ObjectId(build_id)
    build_info = collection_building.find_one({'_id': obj_id})
    if build_info:
        build_info['_id'] = str(build_info['_id'])
        build_info['factory_id'] = str(build_info['factory_id'])
        return build_info

# GET Request Method for user
@router.get("/get_building")
async def get_build_lis() :
    build_lis = list_serial_build(collection_building.find())
    return build_lis

@router.put("/change_building_detail")
async def put_building_detail(detail : BuildingDetail):
    which_building = collection_building.find_one({'_id' : ObjectId(detail.building_id)})

    if which_building :
        collection_building.update_one({'_id' : ObjectId(detail.building_id)},{'$set': {'building_detail' : detail.building_detail}})
        collection_building.update_one({'_id' : ObjectId(detail.building_id)},{'$set': {'building_length' : detail.building_length}})
        collection_building.update_one({'_id' : ObjectId(detail.building_id)},{'$set': {'building_width' : detail.building_width}})
    else:
        raise HTTPException(status_code=404, detail=f"User '{username_veri}' not found.")

#POST Request Method
@router.post("/post_building")
async def post_build_lis(build: Building):
    build_doc = dict(build)
    collection_building.insert_one(build_doc)

#Delete Building and all about it
@router.delete("/building/{building_id}")
async def delete_building(id_building : BuildingId):
    
    find_history_by_building_id = collection_history.find({'building_id' : id_building.build_id})

    for each_history in find_history_by_building_id :
        each_history_id = each_history['_id']
        await delete_history(HistoryId(histo_id = str(each_history_id)))
    
    collection_building.find_one_and_delete({'_id' : ObjectId(id_building.build_id)})

#-------------------------------------------------------History-----------------------------------------------------

@router.get("/get_history")
async def get_history(id_building : str):
    histo_list = []

    find_history = collection_history.find({"building_id" : str(id_building)})

    for each_history in find_history:
        each_history['_id'] = str(each_history['_id'])
        histo_list.append(each_history)
    
    return histo_list

@router.post("/post_history")
async def post_history(id_building : BuildingId) :
    current_datetime_utc = datetime.utcnow()
    timezone_bangkok = pytz.timezone('Asia/Bangkok')
    current_datetime_bangkok = current_datetime_utc.replace(tzinfo=pytz.utc).astimezone(timezone_bangkok)
    history = History(
        create_date=current_datetime_bangkok.strftime("%d-%m-%Y"),
        create_time=current_datetime_bangkok.strftime("%H:%M:%S"),
        building_id=str(id_building.build_id)
    )
    history_doc = dict(history)
    collection_history.insert_one(history_doc)

@router.delete("/delete_history")
async def delete_history(id_histo : HistoryId):

    find_image_by_history_id = collection_Image.find({'history_id' : id_histo.histo_id})

    for each_image in find_image_by_history_id :
        each_image_id = each_image['_id']
        await delete_image_lis(ImageId(image_id = str(each_image_id)))
    
    collection_history.find_one_and_delete({'_id' : ObjectId(id_histo.histo_id)})

#-------------------------------------------------------Image-------------------------------------------------------

# GET Request Method for image when need to show image which have defect
@router.get("/get_image")
async def get_image_lis(history_id : str) :
    image_list = []

    which_history_id = history_id

    find_image_by_history_id = {'history_id' : str(which_history_id)}
    which_image = collection_Image.find(find_image_by_history_id)
    for each_image in which_image:
        which_image_id = each_image['_id']
        find_defectlo_by_image_id = {'image_id' : ObjectId(which_image_id)}
        defect_count = collection_DefectLocation.count_documents(find_defectlo_by_image_id)
        which_image_path = each_image['image_path']
        image_list.append({"image_id" : str(which_image_id), "image_path": which_image_path})

    return image_list

#POST Request Method
@router.post("/post_image")
async def post_image_lis(img: Image):
    image_doc = dict(img)
    collection_Image.insert_one(image_doc)

# Delete Request Method for image
@router.delete("/image/{image_path}")
async def delete_image_lis(id_image : ImageId):

    tasks = []
    which_image_id = id_image.image_id
    tasks.append(delete_defectlo_lis(ImageId(image_id = str(which_image_id))))
    
    await asyncio.gather(*tasks)

    collection_Image.find_one_and_delete({'_id' : ObjectId(str(which_image_id))})


#-------------------------------------------------------DefectLocation-------------------------------------------------------
# GET Request Method by image_id
@router.get("/get_defectLocation")
async def get_defectlo_lis(image_id : str) :

    image_id_in_defect = {'image_id' : ObjectId(image_id)}
    defectlo_lis = list_serial_defectlo(collection_DefectLocation.find(image_id_in_defect))
    return defectlo_lis

#POST Request Method for redefine the defect square
@router.post("/post_defectLocation_for_redefine")
async def post_defectlo_lis_redefine(defect_with_image: DefectLocationWithImage):
    Image_post_id = ObjectId(defect_with_image.Image_post_id)
    defectlos = defect_with_image.defectlos

    for defectlo in defectlos:
        defectlocation_doc = dict(defectlo)
        defectlocation_doc['image_id'] = ObjectId(Image_post_id)
        class_type = defectlocation_doc['class_type']
        class_data = collection_Defect.find({"defect_class" : class_type})
        for each_doc in class_data:
            class_name = each_doc['defect_class_name']
        defectlocation_doc['class_name'] = class_name
        collection_DefectLocation.insert_one(defectlocation_doc)
        defectlocation_doc.clear()


#POST Request Method for use model detection
#Use image path for parameter
@router.post("/post_defectLocation_for_model")
async def post_defectlo_lis_model(build_path : BuildingPath):

    #get position's image path and model path
    img_path = os.path.join(build_path.building_path) #image path for model
    model_path = os.path.join('bestv3.pt')
    model = YOLO(model_path)
    cap = cv2.VideoCapture(img_path)

    find_image = collection_Image.find({},{"image_path": build_path.building_path})

    for each_doc in find_image:
        image_id = ObjectId(each_doc['_id'])

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
async def delete_defectlo_lis(id_image : ImageId):
    defectloc_image = collection_DefectLocation.find({"image_id": ObjectId(id_image.image_id)})
    
    for each_doc in defectloc_image:
        defectlo_id = each_doc['_id']
        collection_DefectLocation.find_one_and_delete({"_id": ObjectId(defectlo_id)})
    
    
#-------------------------------------------------------Permission-------------------------------------------------------
#GET Request Method
@router.get("/get_permission_factory")
async def get_permis_factory(facto_id : str) :
    obj_id = ObjectId(facto_id)
    find_permission = collection_Permission.find({"factory_id" : obj_id})

    user_list = []
    for each_permission in find_permission:
        that_user_id = str(each_permission['user_id'])
        which_user = {'_id' : ObjectId(that_user_id)}
        find_user = collection_user.find_one(which_user)
        print(find_user)
        if find_user:
            find_user['_id'] = str(find_user['_id'])
            user_list.append(find_user)

    return user_list

#Get Method for show verified user who dont have permission in that factory
@router.get("/get_not_permissin_factory")
async def get_no_permis_facto(facto_id : str):
    obj_id = ObjectId(facto_id)
    verified_users = collection_user.find({"is_verified": True, "is_admin" : False})

    user_list = []
    for each_verified_users in verified_users:
        each_verified_users['_id'] = str(each_verified_users['_id']) 
        user_list.append(each_verified_users)

    find_permission = collection_Permission.find({"factory_id" : obj_id})
    for each_permission in find_permission:
        that_user_id = str(each_permission['user_id'])
        that_user_id = str(each_permission['user_id'])
        for user in user_list:
            if user['_id'] == that_user_id:
                user_list.remove(user)
    
    return user_list

#Post Request Method
@router.post("/post_permission")
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
@router.delete("/permis_user")
async def delete_user_permis(permis_username : UsernameInput):
    print('delete_user_permis' + ' : ' + permis_username.username)
    who_user_username = {'username' : str(permis_username.username)}
    who_user = collection_user.find(who_user_username)

    for that_user in who_user :
        who_user_id = that_user['_id']
        which_permis = collection_Permission.find({'user_id' : ObjectId(who_user_id)})
        for each_permis in which_permis:
            collection_Permission.find_one_and_delete(each_permis)

@router.delete("/permis_facto/{permis_factory}")
async def delete_factory_permis(id_facto : FactoryId):

    which_permis = collection_Permission.find({'factory_id' : ObjectId(id_facto.facto_id)})
    for each_permis in which_permis:
        collection_Permission.find_one_and_delete(each_permis)


#-------------------------------------------------------Defect-------------------------------------------------------
# GET Request Method
# @router.get("/get_defect")
# async def get_defec_lis() :
#     defec_lis = list_serial_defec(collection_Defect.find())
#     return defec_lis

# #POST Request Method
# @router.post("/post_defect")
# async def post_defec_lis(defec: Defect):
#     defect_doc = dict(defec)
#     collection_Defect.insert_one(_doc)

# @router.put("/{id}")
# async def put_todo(id: str, todo: Todo):
#     collection_name.find_one_and_update({"_id": ObjectId(id)}, {"$set": dict(todo)})

# @router.delete("/{id}")
# async def delete_todo(id:str):
#     collection_name.find_one_and_delete({"_id": ObjectId(id)})

#-------------------------------------------------------Video-------------------------------------------------------
@router.post("/upload_video_file")
async def upload_video(fileList: List[UploadFile]):
    file_path = str(uuid.uuid4())
    os.makedirs(f"data/video/{file_path}", exist_ok=True)
    for file in fileList:
        file_dir = f"data/video/{file_path}/{file.filename}"
        try :
            contents = await file.read()
            with open(file_dir,"wb") as f:
                f.write(contents)
        except Exception as e:
            return {"message": f"There was an error uploading the file {e}"}
        finally:
            await file.close()

    return {"path": f"data/video/{file_path}"}

@router.post("/extract_video")
async def extract_video(path: ExtractVideo):
    video_paths = glob.glob(f'{path.input_dir}/*.mp4')
    fps = 1
    frame_count = 0
    digits = len(str(len(video_paths) * 323))

    for video_path in video_paths:
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            print(f"Error: Could not open video file '{video_path}'.")
            continue

        frame_interval = int(cap.get(cv2.CAP_PROP_FPS) / fps)

        while cap.isOpened():
        # Read a frame from the video
            ret, frame = cap.read()

        # Check if the frame was read successfully
            if not ret:
                break

        # Increment frame count
            frame_count += 1

        # Process the frame (you can perform any operations here if needed)
        # For example, you can save the frame to a file
            frame_filename = f'{path.output_dir}/{str(frame_count).zfill(digits)}.jpg'
            cv2.imwrite(frame_filename, frame)

        # Skip frames to match the desired frame extraction rate
            for _ in range(frame_interval - 1):
                cap.grab()

    # Release the VideoCapture object
        cap.release()

    shutil.rmtree(path.input_dir)

    return {"message": "extract video complete"}
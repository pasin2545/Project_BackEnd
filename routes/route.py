from fastapi import APIRouter
from models.modl import User,Factory,Building,Image,Defect,DefectLocation
from config.database import collection_user,collection_building,collection_factory,collection_Image,collection_DefectLocation,collection_Defect
from schema.schemas import list_serial_user,list_serial_build,list_serial_factory,list_serial_image,list_serial_defectlo,list_serial_defec
from bson import ObjectId

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
# GET Request Method
@router.get("/Get Building")
async def get_build_lis() :
    build_lis = list_serial_build(collection_building.find())
    return build_lis

#POST Request Method
@router.post("/Post Building")
async def post_build_lis(build: Building):
    collection_building.insert_one(dict(build))


#-----Image-----
# GET Request Method
@router.get("/Get Image")
async def get_image_lis() :
    img_lis = list_serial_image(collection_Image.find())
    return img_lis

#POST Request Method
@router.post("/Post Image")
async def post_image_lis(img: Image):
    collection_Image.insert_one(dict(img))


#-----DefectLocation-----
# GET Request Method
@router.get("/Get DefectLocation")
async def get_defectlo_lis() :
    defectlo_lis = list_serial_defectlo(collection_DefectLocation.find())
    return defectlo_lis

#POST Request Method
@router.post("/Post DefectLocation")
async def post_defectlo_lis(defectlo: DefectLocation):
    collection_DefectLocation.insert_one(dict(defectlo))


#-----Defect-----
# GET Request Method
@router.get("/Get Defect")
async def get_defec_lis() :
    defec_lis = list_serial_defec(collection_Defect.find())
    return defec_lis

#POST Request Method
@router.post("/Post Defect")
async def post_defec_lis(defec: Defect):
    collection_Defect.insert_one(dict(defec))

# @router.put("/{id}")
# async def put_todo(id: str, todo: Todo):
#     collection_name.find_one_and_update({"_id": ObjectId(id)}, {"$set": dict(todo)})

# @router.delete("/{id}")
# async def delete_todo(id:str):
#     collection_name.find_one_and_delete({"_id": ObjectId(id)})
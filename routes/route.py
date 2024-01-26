from fastapi import APIRouter
from models.modl import User,Factory,Building
from config.database import collection_user,collection_building,collection_factory
from schema.schemas import list_serial_user,list_serial_build,list_serial_factory
from bson import ObjectId

router = APIRouter()

#GET Request Method
@router.get("/Get User")
async def get_usr_lis() :
    usr_lis = list_serial_user(collection_user.find())
    return usr_lis

#POST Request Method
@router.post("/Post User")
async def post_usr_lis(usr: User):
    collection_user.insert_one(dict(usr))

# GET Request Method
@router.get("/Get Factory")
async def get_facto_lis() :
    facto_lis = list_serial_factory(collection_factory.find())
    return facto_lis

#POST Request Method
@router.post("/Post Factory")
async def post_facto_lis(facto: Factory):
    collection_factory.insert_one(dict(facto))


# GET Request Method
@router.get("/Get Building")
async def get_build_lis() :
    build_lis = list_serial_build(collection_building.find())
    return build_lis

#POST Request Method
@router.post("/Post Building")
async def post_build_lis(build: Building):
    collection_building.insert_one(dict(build))

# @router.put("/{id}")
# async def put_todo(id: str, todo: Todo):
#     collection_name.find_one_and_update({"_id": ObjectId(id)}, {"$set": dict(todo)})

# @router.delete("/{id}")
# async def delete_todo(id:str):
#     collection_name.find_one_and_delete({"_id": ObjectId(id)})
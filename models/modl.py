from pydantic import BaseModel,Field

class User(BaseModel):
    username : str
    password : str
    is_admin : bool
    user_verification_file_path : str

class Factory(BaseModel):
    factory_name : str
    factory_details : str

class Building(BaseModel):
    building_name : str
    building_detail : str
    building_length : float
    building_width : float
    data_location : str
    defect_sum : int
    each_defect_type_sum : str
    factory_id: Object = None

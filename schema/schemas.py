def individual_serial_user(usr) -> dict:
    return {
        "user_id" : str(usr["_id"]),
        "username" : usr["username"],
        "password" : usr["password"],
        "is_admin" : usr["is_admin"],
        "user_verification_file_path" : usr["user_verification_file_path"]
    }

def individual_serial_factory(facto) -> dict:
    return {
        "factory_id" : str(facto["_id"]),
        "factory_name" : facto["factory_name"],
        "factory_details" : facto["factory_details"],
    }

def individual_serial_build(build) -> dict:
    return {
        "building_id" : str(build["_id"]),
        "building_name" : build["building_name"],
        "building_detail" : build["building_detail"],
        "building_length" : build["building_length"],
        "building_width" : build["building_width"],
        "data_location" : build["data_location"],
        "defect_sum" : build["defect_sum"],
        "each_defect_type_sum" : build["each_defect_type_sum"],
    }

def individual_serial_image(img) -> dict:
    return{
        "image_id" : str(img["_id"]),
        "image_path" : img["image_path"],
        "stitched_location_x" : img["stitched_location_x"],
        "stitched_location_y" : img["stitched_location_y"]
    }

def individual_serial_defectlo(defectlo) -> dict:
    return{
        "defect_location_id" : str(defectlo["_id"]),
        "x" : defectlo["x"],
        "y" : defectlo["y"],
        "w" : defectlo["w"],
        "h" : defectlo["h"]
    }

def individual_serial_defec(defec) -> dict:
    return{
        "defect_class" : defec["defect_class"],
        "defect_class_name" : defec["defect_class_name"]
    }


def list_serial_user(usr_lis) -> list :
    return [individual_serial_user(usr) for usr in usr_lis]

def list_serial_factory(facto_lis) -> list :
    return [individual_serial_factory(facto) for facto in facto_lis]

def list_serial_build(build_lis) -> list :
    return [individual_serial_build(build) for build in build_lis]

def list_serial_image(img_lis) -> list :
    return [individual_serial_image(img) for img in img_lis]

def list_serial_defectlo(defectlo_lis) -> list :
    return [individual_serial_defectlo(defectlo) for defectlo in defectlo_lis]

def list_serial_defec(defec_lis) -> list :
    return [individual_serial_defec(defec) for defec in defec_lis]


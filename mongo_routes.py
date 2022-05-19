from bson.objectid import ObjectId
from route_config import *
from auth_routes import auth_required
from flask import json, jsonify, make_response


@app.route("/getUser", methods=["GET"])
@auth_required
def getUser(uid):
    profileParams = ['email', 'username']

    objID = ObjectId(uid)
    if not objID:
        return make_response(jsonify({'message': 'missing uid'}), 400)

    user = db.users.find_one_or_404({"_id": objID})

    profile = {}
    profile["uid"] = str(objID)
    for key in profileParams:
        profile[key] = ''
        if key in user:
            profile[key] = user[key]

    return make_response(jsonify({'profile': profile}), 200)


@app.route("/addImage", methods=['POST'])
@auth_required
def addImage(uid):
    image_url = ""
    image_name = ""
    if request.is_json:
        try:
            json_data = request.get_json()
            image_url = json_data['image_url']
            image_name = json_data['image_name']
        except:
            return make_response(jsonify({"message": "Error, must include image url and name"}), 400)
    objID = ObjectId(uid)
    if not objID:
        return make_response(jsonify({'message': 'missing uid'}), 400)
    prev_image = db.images.find_one({"uid": objID, "image_name": image_name})
    if prev_image:
        return make_response(jsonify({'message': 'error, image name already exists associated to user'}), 406)
    new_image = db.images.insert_one({
        "uid": objID,
        "image_name": image_name,
        "uploaded_image": image_url
    })
    return make_response(jsonify({"message": "Successfully added image!"}), 200)


@app.route("/addSegmentedImage", methods=['POST'])
@auth_required
def addSegmented(uid):
    image_url = ""
    image_name = ""
    if request.is_json:
        try:
            json_data = request.get_json()
            image_url = json_data['image_url']
            image_name = json_data['image_name']
        except:
            return make_response(jsonify({"message": "Error, must include image url and name"}), 400)
    objID = ObjectId(uid)
    if not objID:
        return make_response(jsonify({'message': 'missing uid'}), 400)
    prev_image = db.images.find_one_or_404(
        {"uid": objID, "image_name": image_name})
    prev_image = db.images.find_one_and_update(
        {"uid": objID, "image_name": image_name},
        {'$set': {"segmented_image": image_url}}
    )
    return make_response(jsonify({"message": "Successfully added segmented image url!"}), 200)


@app.route("/deleteImage", methods=['POST'])
@auth_required
def deleteImage(uid):
    image_name = ""
    if request.is_json:
        try:
            json_data = request.get_json()
            image_name = json_data['image_name']
        except:
            return make_response(jsonify({"message": "Error, must include image name"}), 400)
    objID = ObjectId(uid)
    if not objID:
        return make_response(jsonify({'message': 'missing uid'}), 400)
    prev_image = db.images.find_one_or_404(
        {"uid": objID, "image_name": image_name})
    prev_image = db.images.find_one_and_delete(
        {"uid": objID, "image_name": image_name}
    )
    return make_response(jsonify({"message": "Successfully deleted  image!"}), 200)


@app.route("/deleteSegmentedImage", methods=['POST'])
@auth_required
def deleteSegmented(uid):
    image_url = ""
    image_name = ""
    if request.is_json:
        try:
            json_data = request.get_json()
            image_name = json_data['image_name']
        except:
            return make_response(jsonify({"message": "Error, must include image name"}), 400)
    objID = ObjectId(uid)
    if not objID:
        return make_response(jsonify({'message': 'missing uid'}), 400)
    prev_image = db.images.find_one_or_404(
        {"uid": objID, "image_name": image_name})
    prev_image = db.images.find_one_and_update(
        {"uid": objID, "image_name": image_name},
        {'$unset': {"segmented_image": ""}}
    )
    return make_response(jsonify({"message": "Successfully deleted segmented image url!"}), 200)


@app.route("/getImages", methods=['GET'])
@auth_required
def getImages(uid):
    objID = ObjectId(uid)
    images = db.images.find({"uid": objID})
    usersImages = []
    for image in images:
        # print(image)
        serializedImage = image
        serializedImage['_id'] = str(image['_id'])
        serializedImage['uid'] = str(image['uid'])
        usersImages.append(serializedImage)
    return make_response(jsonify({"images": usersImages}), 200)

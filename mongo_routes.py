from bson.objectid import ObjectId
from route_config import *
from auth_routes import auth_required
from flask import json, jsonify, make_response
from bson.objectid import ObjectId
import json
import os
import requests
import re


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
        "uploaded_image": image_url,
        "public": False
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


@app.route("/findAssociated", methods=['POST'])
@auth_required
def findAssociated(uid):
    objID = ObjectId(uid)
    image_name = ""
    if request.is_json:
        try:
            json_data = request.get_json()
            image_name = json_data['image_name']
        except:
            return make_response(jsonify({"message": "Error, must include image name"}), 400)
    db_image = db.images.find_one_or_404(
        {"uid": objID, "image_name": image_name})
    image_url = ''
    try:
        image_url = db_image['uploaded_image']
    except:
        return make_response(jsonify({"message": "Error, no image associated"}), 400)

    lykdatRes = requests.post('https://cloudapi.lykdat.com/v1/global/search', data={
        'api_key': os.environ.get("LYKDAT_API_KEY", ""),
        'image_url': image_url
    })
    if lykdatRes.status_code >= 400:
        return make_response(jsonify({"message": "Error, LykDat API Failed"}), 500)
    print(lykdatRes)
    lykdatData = lykdatRes.json()
    print(lykdatData)

    # with open('lykdatResponse.json') as f:
    #     lykdatData = json.load(f)

    lykdatData = lykdatData['data']['result_groups']
    print(lykdatData)

    def filterArr(group):
        data = group["similar_products"]
        imageRegEx = '^.*.(jpe?g|png|JPE?G)$'
        filteredData = [el for el in data if re.search(
            imageRegEx, el.get("matching_image", ""))]
        filteredData = filteredData[0:10]
        return filteredData

    filteredData = list(map(lambda group: filterArr(group), lykdatData))

    default_category_names = list(
        map(lambda num: "Category " + str(num + 1), range(len(filteredData))))
    updatedData = db.images.find_one_and_update(
        {"uid": objID, "image_name": image_name},
        {'$set': {"similarClothes": filteredData,
                  "categoryNames": default_category_names}}
    )
    return make_response(jsonify({"message": "Successfully added"}), 200)


@app.route("/getAssociated", methods=['GET'])
@auth_required
def getAssociated(uid):
    objID = ObjectId(uid)
    image_name = ""
    if request.is_json:
        try:
            json_data = request.get_json()
            image_name = json_data['image_name']
        except:
            return make_response(jsonify({"message": "Error, must include image name"}), 400)
    db_image = db.images.find_one_or_404(
        {"uid": objID, "image_name": image_name})
    similarClothes = db_image.get("similarClothes", [])
    similarCategories = db_image.get("categoryNames", [])
    if (len(similarClothes) <= 0 or len(similarCategories) <= 0):
        return make_response(jsonify({"message": "No associated clothes to picture"}),
                             400)

    return make_response(jsonify({
        "similarClothes": similarClothes,
        "similarCategories": similarCategories}),
        200)


@app.route("/getAssociatedCategories", methods=["GET"])
@auth_required
def getAssociatedCategories(uid):
    objID = ObjectId(uid)
    image_name = ""
    if request.is_json:
        try:
            json_data = request.get_json()
            image_name = json_data['image_name']
        except:
            return make_response(jsonify({"message": "Error, must include image name"}), 400)
        db_image = db.images.find_one_or_404(
            {"uid": objID, "image_name": image_name})
        try:
            categories = db_image["categoryNames"]
        except:
            return make_response(jsonify({"message": "Error, no categories"}), 404)
        return make_response(jsonify({"categories": categories}), 200)


@app.route("/updateAssociatedCategory", methods=['POST'])
@auth_required
def updateAssociatedCategory(uid):
    objID = ObjectId(uid)
    image_name = ""
    index = ""
    new_name = ""
    if request.is_json:
        try:
            json_data = request.get_json()
            image_name = json_data['image_name']
            index = json_data["index"]
            new_name = json_data["new_name"]
        except:
            return make_response(jsonify({"message": "Error, must include image name, index to update, and new name"}), 400)
    db_image = db.images.find_one_or_404(
        {"uid": objID, "image_name": image_name})
    db_image = db.images.find_one_and_update(
        {"uid": objID, "image_name": image_name},
        {'$set': {"categoryNames."+str(index): new_name}}
    )
    return make_response(jsonify({"message": "Successfully updated category name"}), 200)


@app.route("/updatePublic", methods=['POST'])
@auth_required
def updatePublic(uid):
    objID = ObjectId(uid)
    image_name = ""
    new_val = False
    if request.is_json:
        try:
            json_data = request.get_json()
            image_name = json_data['image_name']
            new_val = json_data['val']
        except:
            return make_response(jsonify({"message": "Error, must include image name and val"}), 400)
    db_image = db.images.find_one_or_404(
        {"uid": objID, "image_name": image_name})
    prev_image = db.images.find_one_and_update(
        {"uid": objID, "image_name": image_name},
        {'$set': {"public": new_val}}
    )
    return make_response(jsonify({"message": "Successfully changed public value"}), 200)


@app.route("/getPublicImages", methods=['GET'])
@auth_required
def getPublic(uid):
    objID = ObjectId(uid)
    images = db.images.find({"uid": {'$ne': objID}, "public": True})
    publicImages = []
    for image in images:
        # print(image)
        serializedImage = image
        serializedImage['_id'] = str(image['_id'])
        serializedImage['uid'] = str(image['uid'])
        publicImages.append(serializedImage)
    return make_response(jsonify({"images": publicImages}), 200)

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
    for key in profileParams:
        profile[key] = ''
        if key in user:
            profile[key] = user[key]

    return make_response(jsonify({'profile': profile}), 200)

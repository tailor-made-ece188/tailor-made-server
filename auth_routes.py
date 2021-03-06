# from datetime import date
import os
import datetime
# from posix import environ
from route_config import *
from flask import jsonify, make_response, request
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from bson.objectid import ObjectId
import jwt
import datetime

# TODO: USE IS_JSON and GETJSON


def auth_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        auth_token = None
        if 'auth-token' in request.headers:
            auth_token = request.headers['auth-token']
        if not auth_token:
            return make_response(jsonify({'message': 'no auth token'}), 401)
        try:
            jwt_data = jwt.decode(auth_token, os.environ.get(
                "PASSWORD_SALT"), algorithms=["HS256"])
            uid = ObjectId(jwt_data['_id'])
            db.users.find_one_or_404({"_id": uid})
        except:
            return make_response(jsonify({"message": 'token is invalid'}), 401)

        print('authenticated')
        return f(uid, *args, **kwargs)
    return decorator


@app.route('/validateToken', methods=['GET'])
def validate_token():
    headers = request.headers
    auth_token = headers.get('auth-token')
    jwt_data = None
    try:
        jwt_data = jwt.decode(auth_token, os.environ.get(
            "PASSWORD_SALT"), algorithms=["HS256"])
        uid = ObjectId(jwt_data['_id'])
        user = db.users.find_one({"_id": uid})
    except:
        return make_response(jsonify({"message": f"decode token failed, {jwt_data}"}), 401)
    if not user:
        return make_response(jsonify({"message": 'user not found'}), 401)
    return jsonify({"message": 'validation success'})


@app.route('/register', methods=['POST'])
def registerUser():
    request_data = request.args
    if request.is_json:
        request_data = request.get_json()
    user_pass = request_data.get("password")
    user_email = request_data.get("email")
    user_username = request_data.get("username")
    if user_pass is None or user_email is None or user_username is None:
        return make_response(jsonify({"message": "Error, must register with username, email, and password"}), 400)

    prev_user = db.users.find_one({"email": user_email})
    if prev_user:
        return make_response(jsonify({"message": "Error, email is taken"}), 409)
    prev_username = db.users.find_one({"username": user_username})
    if prev_username:
        return make_response(jsonify({"message": "Error, username is taken"}), 409)

    hashed_password = generate_password_hash(user_pass, method='sha256')
    new_user = db.users.insert_one({
        "email": user_email,
        "password": hashed_password,
        "username": user_username
    })
    return jsonify({"message": "User successfully registered"})


@app.route('/loginUsername', methods=['POST'])
def login_user():
    auth = request.authorization
    if request.is_json:
        print(request.get_json())
        auth = request.get_json()['authorization']
        # auth = request.get_json()['authorization']
    if not auth or not auth.username or not auth.password:
        return make_response(jsonify({'message': 'Missing authorization credentials'}),  401)
    print("auth.username is: " + auth.username)
    user = db.users.find_one_or_404({"username": auth.username})
    print(user)
    if check_password_hash(user["password"], auth.password):
        jwt_token = jwt.encode({
            '_id': str(user['_id']),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=4)
        },
            os.environ.get("PASSWORD_SALT"), "HS256")
        return jsonify({'jwt_token': jwt_token})
    return make_response(jsonify({'message': 'Invalid username or password'}),  401)

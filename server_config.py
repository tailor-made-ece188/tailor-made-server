import os
from route_config import *
from auth_routes import *
from mongo_routes import *

env = os.getenv('PRODUCTION', 'testing')
if env == 'testing':
    app.debug = True

host = os.environ.get("IP", '0.0.0.0')
port = int(os.environ.get("PORT", 8080))

if __name__ == "__main__":
    app.run(host=host, port=port)

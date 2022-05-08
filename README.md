# Tailor-Made Backend Server

Our server is made with Flask, and uses MongoDB Atlas as its database.

## Developer Guide:

* If you don't have your virtual environment set up...

```sh
# making a virtual environment
$python3 -m venv env

# always activate your virtual environment!!
# to activate
$source env/bin/activate
# to deactivate
$deactivate

#installing dependencies
pip install -r requirements.txt
#updating dependency list when adding new ones
pip freeze > requirements.txt

# to run server
python3 server_config.py


# Forecaster
Flask server for forecast and visualise predict for ClickHouse database
## Run application (development mode)
### On Linux
Install requirements:
````
pip3 install -r ./requirements.txt
````

Run Flask server (local):
````
export FLASK_APP=server && flask run
````

Run Flask server (local network):
````
export FLASK_APP=server && flask run --host=0.0.0.0
````
### On Windows
Create and activate virtual enviroment (if py.exe on PATH):

````
py.exe -m pip3 install venv
py.exe -m venv ${ENV_NAME}
.\${ENV_NAME}\Scripts\activate
````
Install requirements:
````
pip3 install -r ./requirements.txt
````
Run Flask server (local):
````
flask --app=server run
````
Run Flask server (local network):
````
flask --app=server run --host=0.0.0.0
````

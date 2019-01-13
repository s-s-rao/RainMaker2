import os
import pymysql
from hashlib import sha256
from warnings import filterwarnings
from flask import Flask, json, request, make_response

app = Flask(__name__)
meta = json.load(open("meta.json"))
filterwarnings('ignore', category = pymysql.Warning)
databaseCursor = pymysql.connect(
    host = meta["DatabaseIPAddress"],
    user = meta["CSPDatabaseUsername"],
    passwd = meta["CSPDatabasePassword"],
    port = meta["DatabasePort"],
    autocommit = True
).cursor(pymysql.cursors.DictCursor)
databaseCursor.execute("use {};".format(meta["CSPDatabaseName"]))

#tenantId - sessionKey mapping
tenantSessionKeys = {}

@app.route('/')
def hello_world():
    return 'This is the Dashboard'

@app.route('/tenantsignup', methods=['POST'])
def tenantSignup():
    tenantName, password = request.json["tenantName"], request.json["password"]

    # add to Users table
    databaseCursor.execute("select Subnet as subnet from Users;")
    results = databaseCursor.fetchall()
    maxSubnet = max([i["subnet"].split(".")[2] for i in results])
    databaseCursor.execute("select Subnet as subnet from Users where Id = 0;")  
    CSPSubnet = databaseCursor.fetchone()["subnet"].split(".")[:2]
    newSubnet = CSPSubnet.extend([maxSubnet + 1, 0])
    newSubnet = ".".join(newSubnet) + "/24"

    h = sha256(bytes(password, "utf-8")).hexdigest()
    query = """insert into Users (Name, PasswordHash, Subnet)
		values ({}, {}, {});""".format(tenantName, h, newSubnet)
    databaseCursor.execute(query)
    
    responseMessage = {
        "status": "success",
        "message": ""
    }
    response = app.response_class(
        response = json.dumps(responseMessage),
        status = 200,
        mimetype = 'application/json'
    )
    return response

@app.route('/tenantlogin', methods=['POST'])
def tenantLogin():
    tenantName, password = request.json["tenantName"], request.json["password"]
    h = sha256(bytes(password, "utf-8")).hexdigest()
    databaseCursor.execute("select PasswordHash as ph from Users where Name='{}'".format(tenantName))
    if databaseCursor.fetchone()["ph"] == h:
        responseMessage = {
            "status": "success",
            "message": "Valid login credentials"
        }
    else:
        responseMessage = {
            "status": "error",
            "message": "Invalid login credentials"
        }
    response = app.response_class(
        response = json.dumps(responseMessage),
        status = 400,
        mimetype = 'application/json'
    )
    return response

@app.route('/tenantinitialize')
def tenantInitialize(webRole, workerRole, noOfWebRoles, noOfWorkerRoles):
    if not os.path.exists(directory):
        os.makedirs(directory)
    

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port=meta["AppPort"])
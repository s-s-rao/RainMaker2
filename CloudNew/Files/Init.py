import json
import os
import subprocess
import pymysql
import pymysql.cursors
from hashlib import sha256
from warnings import filterwarnings

def readConfigurations(confPath):
	#read the configuration file
	with open(confPath, "r") as confFile:
		confs = json.load(confFile)

	meta = {
		"DatabaseIPAddress": confs["IPAddresses"]["Database"],
		"DatabasePort": confs["Ports"]["Database"]["AppPort"],
		"CSPDatabaseName": confs["Database"]["CSPDatabaseName"],
		"CSPDatabaseUsername": confs["Database"]["CSPDatabaseUsername"],
		"CSPDatabasePassword": confs["Database"]["CSPDatabasePassword"]
	}
	#write Database IP, Port, CSP Database details to LoadBalancer, Dashboard and HealthMonitor.
	pathAndAppPort = [
		("./Files/LoadBalancer/meta.json", confs["Ports"]["LoadBalancer"]["AppPort"]),
		("./Files/Dashboard/meta.json", confs["Ports"]["Dashboard"]["AppPort"]),
		("./Files/HealthMonitor/meta.json", confs["Ports"]["HealthMonitor"]["AppPort"])
	]
	for path, appPort in pathAndAppPort:
		meta["AppPort"] = appPort
		with open(path, "w+") as f:
			f.write(json.dumps(meta, indent=4))

	#write Database IP, Port, Tenant Database details to DatabaseAccessController.
	meta = {
		"DatabaseIPAddress": confs["IPAddresses"]["Database"],
		"DatabasePort": confs["Ports"]["Database"]["AppPort"],
		"TenantDatabaseName": confs["Database"]["TenantDatabaseName"], 
		"TenantDatabasePassword": confs["Database"]["TenantDatabasePassword"], 
		"TenantDatabaseUsername": confs["Database"]["TenantDatabaseUsername"],
		"AppPort": confs["Ports"]["DatabaseAccessController"]["AppPort"]
	}
	with open("./Files/DatabaseAccessController/meta.json", "w+") as f:
			f.write(json.dumps(meta, indent=4))

	#write LoadBalancer's IP and port to Host containers
	meta = {
		"LoadBalancerIPAddress": confs["IPAddresses"]["LoadBalancer"],
		"LoadBalancerPort": confs["Ports"]["LoadBalancer"]["AppPort"],
		"AppPort": confs["Ports"]["Host"]["AppPort"]
	}
	with open("./Files/Host/meta.json", "w+") as f:
			f.write(json.dumps(meta, indent=4))

	#write LoadBalancer's + DatabaseAccessController's IP and port to WebRole
	meta = {
		"DatabaseAccessControllerIPAddress": confs["IPAddresses"]["DatabaseAccessController"],
		"DatabaseAccessControllerPort": confs["Ports"]["DatabaseAccessController"]["AppPort"],
		"LoadBalancerIPAddress": confs["IPAddresses"]["LoadBalancer"],
		"LoadBalancerPort": confs["Ports"]["LoadBalancer"]["AppPort"],
		"AppPort": confs["Ports"]["WebRole"]["AppPort"]
		
	}
	with open("./Files/WebRole/meta.json", "w+") as f:
			f.write(json.dumps(meta, indent=4))

	#write DatabaseAccessController's IP to WorkerRole
	meta = {
		"DatabaseAccessControllerIPAddress": confs["IPAddresses"]["DatabaseAccessController"],
		"DatabaseAccessControllerPort": confs["Ports"]["DatabaseAccessController"]["AppPort"],
		"AppPort": confs["Ports"]["WorkerRole"]["AppPort"]
	}
	with open("./Files/WorkerRole/meta.json", "w+") as f:
			f.write(json.dumps(meta, indent=4))

	return confs

def createRainMakerNetwork(IPAddress):
	cmd = "sudo docker network create -d bridge --subnet {} RainMakerNetwork".format(IPAddress)
	os.system(cmd)
	
def createAndInitializeDatabase(IPAddress, databaseConfs, ports):
	cmd = "docker run --network=RainMakerNetwork --ip={} -p {}:{} --name=Database -e MYSQL_ROOT_PASSWORD={} -d mysql:latest".format(IPAddress, ports["ContainerPort"], ports["AppPort"], databaseConfs["DatabaseRootPassword"])
	containerId = subprocess.getoutput(cmd).split("\n")[-1]

	#wait for Database container to initalize (ready to accept connections)
	cmd = """
		while ! mysqladmin ping -h"{}" --silent; do
			sleep 0.1
		done
		echo "Ready"
	""".format(IPAddress)
	subprocess.getoutput(cmd)

	#create Root Database Cursor
	filterwarnings('ignore', category = pymysql.Warning)
	databaseConnection = pymysql.connect(
		host = IPAddress,
		user = "root",
		passwd = databaseConfs["DatabaseRootPassword"],
		port = ports["AppPort"],
		autocommit = True
	)
	databaseCursor = databaseConnection.cursor(pymysql.cursors.DictCursor)

	#create CSP user and Tenant user
	createUsersCMD = "create user '{user}'@'%' identified by '{password}';"
	databaseCursor.execute(createUsersCMD.format(**{
		"user": databaseConfs["CSPDatabaseUsername"],
		"password": databaseConfs["CSPDatabasePassword"]
	}))
	databaseCursor.execute(createUsersCMD.format(**{
		"user": databaseConfs["TenantDatabaseUsername"],
		"password": databaseConfs["TenantDatabasePassword"]
	}))

	#create CSP and Tenant Databases
	createDatabasesCMD = "drop database if exists {database};create database {database};use {database};"
	databaseCursor.execute(createDatabasesCMD.format(**{
		"database": databaseConfs["CSPDatabaseName"]
	}))
	databaseCursor.execute(createDatabasesCMD.format(**{
		"database": databaseConfs["TenantDatabaseName"]
	}))

	privilegesCMD = """
		grant all privileges on {database}.* to '{user}'@'%';
		flush privileges;
	"""
	databaseCursor.execute(privilegesCMD.format(**{
		"database": databaseConfs["TenantDatabaseName"],
		"user": databaseConfs["TenantDatabaseUsername"]
	}))
	databaseCursor.execute(privilegesCMD.format(**{
		"database": "*",
		"user": databaseConfs["CSPDatabaseUsername"]
	}))

	return containerId

def createComponent(componentName, IPAddress, ports):
	os.chdir("./Files/{}".format(componentName))
	os.system("docker build -t flask-{}:latest .".format(componentName.lower()))
	cmd = "docker run --network=RainMakerNetwork --ip={} --name={} -d -p {}:{} flask-{}".format(IPAddress, componentName, ports["ContainerPort"], ports["AppPort"], componentName.lower())
	containerId = subprocess.getoutput(cmd).split("\n")[-1]
	os.chdir("../..")
	return containerId

def createTables(IPAddress, databaseConfs, ports):
	#initialize database handler
	databaseConnection = pymysql.connect(
		host = IPAddress,
		user = databaseConfs["CSPDatabaseUsername"],
		passwd = databaseConfs["CSPDatabasePassword"],
		port = ports["AppPort"],
		autocommit = True
	)
	databaseCursor = databaseConnection.cursor(pymysql.cursors.DictCursor)

	query = "use {};".format(databaseConfs["CSPDatabaseName"])
	databaseCursor.execute(query)

	#create the Users table
	query = """
		create table Users(
			Id SMALLINT,
			Name VARCHAR(50),
			PasswordHash CHAR(64),
			Subnet VARCHAR(18),

			primary key (Id)
		);
	"""
	databaseCursor.execute(query)

	#create the Components table
	query = """
		create table Components(
			ComponentId CHAR(64),
			ComponentName VARCHAR(50),
			IPAddress VARCHAR(15),
			UserId SMALLINT,
			ContainerPort SMALLINT,
			AppPort SMALLINT,
			Type TINYINT,

			primary key (ComponentId),
			foreign key (UserId) references Users(Id)
		);
	"""
	databaseCursor.execute(query)

	#create the Loads table
	query = """
		create table Loads(
			ComponentId CHAR(64),
			LoadValue INT,
			ActiveTime INT,
			CurrentStatus INT,
			Affinity VARCHAR(15),

			primary key (ComponentId),
			foreign key (ComponentId) references Components(ComponentId)
		);
	"""
	databaseCursor.execute(query)

def updateCSPDb(containerIds, confs):
	#initialize database handler
	databaseConnection = pymysql.connect(
		host = confs["IPAddresses"]["Database"],
		user = confs["Database"]["CSPDatabaseUsername"],
		passwd = confs["Database"]["CSPDatabasePassword"],
		port = confs["Ports"]["Database"]["AppPort"],
		autocommit = True
	)
	databaseCursor = databaseConnection.cursor(pymysql.cursors.DictCursor)
	databaseCursor.execute("use {};".format(confs["Database"]["CSPDatabaseName"]))
	
	#insert CSP to Users table
	h = sha256(bytes(confs["CSP"]["Password"], "utf-8")).hexdigest()
	CSPSubnet = ".".join(confs["IPAddresses"]["CSP"].split(".")[:2]) + ".1.0/24"
	query = """
		insert into Users (Id, Name, PasswordHash, Subnet)
		values (0, '{}', '{}', '{}');
	""".format(confs["CSP"]["Username"], h, CSPSubnet)
	databaseCursor.execute(query)
	
	#insert CSP Components to Components table
	query = "insert into Components (ComponentId, ComponentName, IPAddress, UserId, ContainerPort, AppPort, Type) values "
	for componentName in containerIds:
		query += "('{}', '{}', '{}', 0, {}, {}, 0),".format(
			containerIds[componentName],
			componentName,
			confs["IPAddresses"][componentName],
			confs["Ports"][componentName]["ContainerPort"],
			confs["Ports"][componentName]["AppPort"]
		)
	query = query[:-1] + ";"
	databaseCursor.execute(query)

def main():
	confPath = "./conf.json"
	containerIds = {}

	#read the configuration file
	confs = readConfigurations(confPath)

	#create the RainMaker Network
	createRainMakerNetwork(confs["IPAddresses"]["CSP"])

	#create the all the components
	containerIds["Database"] = createAndInitializeDatabase(confs["IPAddresses"]["Database"], confs["Database"], confs["Ports"]["Database"])
	containerIds["Dashboard"] = createComponent("Dashboard", confs["IPAddresses"]["Dashboard"], confs["Ports"]["Dashboard"])
	containerIds["LoadBalancer"] = createComponent("LoadBalancer", confs["IPAddresses"]["LoadBalancer"], confs["Ports"]["LoadBalancer"])
	containerIds["DatabaseAccessController"] = createComponent("DatabaseAccessController", confs["IPAddresses"]["DatabaseAccessController"], confs["Ports"]["DatabaseAccessController"])
	containerIds["HealthMonitor"] = createComponent("HealthMonitor", confs["IPAddresses"]["HealthMonitor"], confs["Ports"]["HealthMonitor"])

	#create CSP tables in CSP Database
	createTables(confs["IPAddresses"]["Database"], confs["Database"], confs["Ports"]["Database"])
	
	#add CSP data to the created tables
	updateCSPDb(containerIds, confs)

main()
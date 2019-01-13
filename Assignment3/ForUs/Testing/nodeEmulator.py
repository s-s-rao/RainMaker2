import requests
import sys
import json
import random
import decimal
import time

# python35 nodeEmulator.py <nodeDataFileName>

with open(sys.argv[1]) as jsonData:
	nodeData = json.load(jsonData)

# python35 nodeEmulator.py <nodeDataFileName> [new | <nodeId>] 
if len(sys.argv) == 3 and sys.argv[2] == "new":
	meta = nodeData["meta"]
	r = requests.post("http://10.10.10.2:80/api/meta", json=meta)
	res = r.json()

	if res["status"] != "success":
		print("Node registration failed")
		sys.exit(0)

	nodeId = res["data"]["nodeId"]
	print("Node registered. Node ID = {}.".format(str(nodeId)))

elif len(sys.argv) == 3:
	nodeId = str(sys.argv[2])


count = 0

while True:
	# time.sleep(20)		# USE THIS TO EXPLAIN THE NEED FOR LOAD-BALANCING
	time.sleep(1)

	sensorData = {
		"nodeId": nodeId,
		"sensorData": {}
	}

	for k,v in nodeData["sensorData"].items():
		sensorData["sensorData"][k] = float(decimal.Decimal(random.randrange(v["min"]*100, v["max"]*100))/100)

	r = requests.post("http://10.10.10.2:80/api/data", json=sensorData)
	resp = r.json()

	if resp["status"] != "success":
		print("Data ingestion failed")
		break

	count += 1
	print(count)
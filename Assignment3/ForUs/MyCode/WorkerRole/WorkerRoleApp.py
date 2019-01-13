from __future__ import print_function
from flask import Flask, json, jsonify, abort, make_response, request, url_for
from datetime import datetime
from flask import render_template
import operator
import sys
import time

app = Flask(__name__)

def eprint(*args, **kwargs):
	print(*args, file=sys.stderr, **kwargs)

@app.errorhandler(404)
def not_found(error):
	return make_response(jsonify({'error': 'Not found'}), 404)

@app.errorhandler(400)
def not_found(error):
	return make_response(jsonify({'error': 'Bad request'}), 400)

successMessage = {
	"status": "success",
	"message": ""
}

structure = {
	"1": {
		"1": {
			"count": 83,
			"average": 39
		},
		"2": {
			"count": 83,
			"average": 289
		}
	},
	"2": {
		"1": {
			"count": 83,
			"average": 32789
		},
		"2": {
			"count": 83,
			"average": 329
		}
	}
}


rollingAverages = {}

@app.route('/api/rollingaverage/node/<string:nodeId>', methods=['POST'])
def updateRollingAverage(nodeId):
	"""Update the rolling average for sensors in given sensor node."""

	#TODO
	if not request.json:
		abort(400)

	# time.sleep(10)	# to show that worker role is active at the moment

	if str(nodeId) not in rollingAverages.keys():
		rollingAverages[str(nodeId)] = {}

	for sensorId, dataValue in request.json.items():
		if sensorId not in rollingAverages[str(nodeId)]:
			rollingAverages[str(nodeId)][str(sensorId)] = {
				"count": 0,
				"average": 0
			}
		temp = rollingAverages[str(nodeId)][str(sensorId)]["average"]*rollingAverages[str(nodeId)][str(sensorId)]["count"]
		temp += dataValue
		rollingAverages[str(nodeId)][str(sensorId)]["count"] += 1
		rollingAverages[str(nodeId)][str(sensorId)]["average"] = temp/rollingAverages[str(nodeId)][str(sensorId)]["count"]

	

	response = app.response_class(
		response = json.dumps(successMessage),
		status = 200,
		mimetype = 'application/json'
	)
	return response

@app.route('/api/rollingaverage/node/<string:nodeId>/sensor/<string:sensorId>', methods=['GET'])
def getRollingAverage(nodeId, sensorId):
	"""View the rolling average for the given sensor in given sensor node."""

	respData = {
		"data": {}
	}

	if not str(nodeId) in rollingAverages.keys():
		abort(404)

	if not str(sensorId) in rollingAverages[str(nodeId)].keys():
		abort(404)

	respData["data"]["nodeId"] = nodeId
	respData["data"]["sensorId"] = sensorId
	respData["data"]["rollingAverage"] = rollingAverages[str(nodeId)][str(sensorId)]["average"]


	response = app.response_class(
		response = json.dumps(respData),
		status = 200,
		mimetype = 'application/json'
	)
	return response

if __name__ == '__main__':
	app.run(threaded=True, debug=True, host='0.0.0.0', port=80)
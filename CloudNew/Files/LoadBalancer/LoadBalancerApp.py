from flask import Flask
import json

app = Flask(__name__)
meta = json.load(open("meta.json"))

@app.route('/')
def hello_world():
    return 'This is the Load Balancer'

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port=meta["AppPort"])
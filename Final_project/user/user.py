
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy 
from flask_marshmallow import Marshmallow
from sqlalchemy.orm.attributes import flag_modified
import os
from sqlalchemy import PickleType
import requests
import re
import sys
from datetime import datetime
import datetime
import pandas as pd
import json
from flask_track_usage.storage.sql import SQLStorage
from flask_track_usage import TrackUsage


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'userdb.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ma = Marshmallow(app)

pstore=SQLStorage(db=db)
t=TrackUsage(app,[pstore])

db.metadata.clear()







def check_timestamp_24(timestamp):
	date_format = '%d-%m-%Y:%S-%M-%H'
	try:
		datetime1=datetime.datetime.strptime(timestamp,date_format)
		value = True
	except ValueError :
		value = False
	if value :
		current = datetime.datetime.utcnow()
		if current <= datetime1 :
			return True
		else :
			return False
	else :
		return False








@app.route('/api/v1/users', methods=['PUT'])
def add_user():
	if(request.method == 'PUT'):
		username = request.json['username']
		password = request.json['password']
		pattern=re.compile(r'\b([0-9a-f]|[0-9A-F]){40}\b')
		dic={}
		dic["table"]="User"
		dic["username"]=username
		dic["password"]=password
		dic["some"]="add_user"
		if(len(username)==0 or len(password)==0):			
			return jsonify({}),400
		response = requests.post(url ='http://18.233.36.130/api/v1/db/read',json=dic)
		result= response.json()
		if((not bool(result)) and (re.search(pattern, password))):
			response = requests.post(url ='http://18.233.36.130/api/v1/db/write',json=dic)
			
			return jsonify({}), 201
		else:
			return jsonify({}), 400
	else:
		return jsonify({}), 405


#2.list all users
@app.route('/api/v1/users', methods=['GET'])
def list_user():
	if(request.method == 'GET'):
		d={}
		d["table"]="User"
		d["some"]="list_user"
		response = requests.post(url ='http://18.233.36.130/api/v1/db/read',json=d)
		result = response.json()
		#print(result)
		
		if(len(result)==0):

			return jsonify({}), 204
		else:
			res=[li['username'] for li in result]
			#print(res)
			#print(response.text)
			return json.dumps(res), 200
			
	else:
		return jsonify({}), 405



#clear db
@t.exclude
@app.route('/api/v1/db/clear', methods=['POST'])
def clear_db():
	if(request.method == 'POST'):
		d={}
		d["table"]="User"
		d["some"]="clear_db"
		response=requests.post(url='http://18.233.36.130/api/v1/db/write',json=d)
		return jsonify({}),200
			
	else:
		return jsonify({}), 405



#2.Delete user
@app.route('/api/v1/users/<username>', methods=['DELETE'])
def remove_user(username):
	if(request.method == 'DELETE'):
		d={}
		d["table"]="User"
		d["some"]="remove_user"
		d["username"]=username
		response=requests.post(url='http://18.233.36.130/api/v1/db/read',json=d)
		result=response.json()
		if(not bool(result)):
			return jsonify({}),400
		else:
			response = requests.post(url ='http://18.233.36.130/api/v1/db/write',json=d)
			return jsonify({}), 200
	else:
		return jsonify({}), 405





#count the number of http requests
@t.exclude
@app.route('/api/v1/_count', methods=['GET'])
def request_count():
	if(request.method == 'GET'):
		count=db.engine.execute('select count(id) from flask_usage').scalar()
		return json.dumps(count),200
		
	else:
		return jsonify({}),405






#reset the request counter
@t.exclude
@app.route('/api/v1/_count', methods=['DELETE'])
def reset_count():
	if(request.method == 'DELETE'):
		db.engine.execute('Delete from flask_usage')
		db.session.commit()
		return jsonify({}),200
	else:
		return jsonify({}),405



	
if __name__ == '__main__':	
	app.run(debug=True, host='0.0.0.0', port=80, threaded=True)

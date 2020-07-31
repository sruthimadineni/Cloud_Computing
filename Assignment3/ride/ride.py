
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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'ridedb.sqlite')
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











#clear db
@t.exclude
@app.route('/api/v1/db/clear', methods=['POST'])
def clear_db():
	if(request.method == 'POST'):
		d={}
		d["table"]="Ride"
		d["some"]="clear_db"
		response=requests.post(url='http://18.233.36.130/api/v1/db/write',json=d)
		return jsonify({}),200
			
	else:
		return jsonify({}), 405







#3.New ride
@app.route('/api/v1/rides', methods=['POST'])
def add_ride():
	if(request.method == 'POST'):
		created_by = request.json['created_by']
		timestamp = request.json['timestamp']
		source = request.json['source']
		destination = request.json['destination']
		if(int(source)==int(destination)):  #check
			return jsonify({}),400		

		if check_timestamp_24(timestamp):
			d={}
			d["table"]="Ride"
			d["created_by"]=created_by
			d["timestamp"]=timestamp
			d["source"]=source
			d["destination"]=destination
			d["some"]="add_ride"
			response = requests.get(url = 'http://my-load-balancer-1909134217.us-east-1.elb.amazonaws.com/api/v1/users' , json = d)
			result=response.json()
			#print(result)
			
			if int(source) in range(199) and int(destination) in range(199):
				if(len(result)==0):
					return jsonify({}), 400
				else:
					#res=[li['username'] for li in result]
					flag=False
					for i in range(len(result)):
						if (str(created_by)==result[i]):
							response_1 = requests.post(url = 'http://18.233.36.130/api/v1/db/write' , json = d)
							flag=True
					if flag==True:
						return jsonify({}),201
					else:
						return jsonify({}),400
			else:
				return jsonify({}),400
					
		else:
			return jsonify({}), 400
	else:
		return jsonify({}),405


#count the number of http requests
@t.exclude
@app.route('/api/v1/_count', methods=['GET'])
def request_count():
	if(request.method == 'GET'):
		count=db.engine.execute('select count(id) from flask_usage').scalar()
		return json.dumps(count),200
		
	else:
		return jsonify({}),405




#count the number of rides
@app.route('/api/v1/rides/count', methods=['GET'])
def ride_count():
	if(request.method == 'GET'):
		count=Ride.query.filter().count()
		print(count)
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







#5.Ride details
@app.route('/api/v1/rides/<rideId>', methods=['GET'])
def ride_details(rideId):
	if(request.method == 'GET'):
		d={}
		d["table"]="Ride"
		d["some"]="ride_details"
		d["rideId"]=rideId
		response = requests.post(url = 'http://18.233.36.130/api/v1/db/read' , json = d)
		result=response.json()
		print(result)
		if(not bool(result)):
			return jsonify({}), 204
		else:
			return response.text, 200
	else:
		return jsonify({}),405

#7.Delete ride
@app.route('/api/v1/rides/<rideId>', methods=['DELETE'])
def delete_ride(rideId):
	if(request.method == 'DELETE'):
		d={}
		d["table"]="Ride"
		d["some"]="delete_ride"
		d["rideId"]=rideId
		response=requests.post(url='http://18.233.36.130/api/v1/db/read',json=d,headers={'Content-type':'application/json','Accept':'text/plain'})
		result = response.json()

		if(not bool(result)):
			return jsonify({}), 400
		else:
			w=requests.post(url='http://18.233.36.130/api/v1/db/write',json=d,headers={'Content-type':'application/json','Accept':'text/plain'})
			return jsonify({}), 200
	else:
		return jsonify({}),405



#6.Join ride 
@app.route('/api/v1/rides/<rideId>', methods=['POST'])
def join_ride(rideId):
	if(request.method == 'POST'):
	
		username = request.json['username']
		d={}
		d["table"]="Ride"
		d["rideId"]=rideId
		d["username"]=username
		d["some"]="join_ride"
		response=requests.get(url='http://my-load-balancer-1909134217.us-east-1.elb.amazonaws.com/api/v1/users',json=d,headers={'Content-type':'application/json','Accept':'text/plain'})
		result = response.json()
		#print(result)
		if(len(result)==0):
			return jsonify({}), 400
		else:
			#res=[li['username'] for li in result]
			flag=False
			for i in range(len(result)):
				if (str(username)==result[i]):
					flag=True
					response_1 = requests.post(url = 'http://18.233.36.130/api/v1/db/read', json = d,headers={'Content-type':'application/json','Accept':'text/plain'})
					value = response_1.json()
					#print(value)
					if(not bool(value)):
						return jsonify({}), 204
					else:
						response_2 = requests.post(url = 'http://18.233.36.130/api/v1/db/write' , json = d,headers={'Content-type':'application/json','Accept':'text/plain'})
					
						return jsonify({}),200
			if flag==True:
				return jsonify({}),201
			else:
				return jsonify({}),400
				
		
			
			
			
	else:
		return jsonify({}),405




#4.upcoming rides
@app.route('/api/v1/rides', methods=['GET'])
def upcoming_rides():
	if(request.method == 'GET'):

		source  = request.args.get('source')
		destination  = request.args.get('destination')
		if(int(source)==int(destination)):  #check
			return jsonify({}),400	
		d={}
		d["table"]="Ride"
		d["some"]="upcoming_rides"
		d["destination"]=destination
		d["source"]=source
		if int(source) in range(199) and int(destination) in range(199):
			response=requests.post(url='http://18.233.36.130/api/v1/db/read',json=d)
			result = response.json()
			#return result,200
			if(len(result)==0):
				return jsonify({}),204

			else:
				return jsonify(result),200

		else:
			return jsonify({}),400
	else:
		return jsonify({}),405


	
if __name__ == '__main__':	
	app.run(debug=True, host='0.0.0.0', port=80, threaded=True)

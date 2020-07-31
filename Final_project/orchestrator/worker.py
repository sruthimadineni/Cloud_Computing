
#!/usr/bin/python
import os
import json
import string
import requests
import datetime
import time
import pika
import random
import re
import docker
import logging
import atexit

from kazoo.client import KazooClient
from kazoo.client import KazooState

from datetime import datetime
from sqlalchemy import *
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker
from sqlalchemy import PickleType
from sqlalchemy.orm.attributes import flag_modified

from flask import Flask, request, jsonify, abort, Response, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from requests.exceptions import HTTPError
from flask_track_usage import TrackUsage
from flask_track_usage.storage.sql import SQLStorage
from apscheduler.schedulers.background import BackgroundScheduler
from multiprocessing import Value


app = Flask(__name__)
ma=Marshmallow(app)


letters = string.ascii_lowercase
dbname = ''.join(random.choice(letters) for i in range(4))

print(dbname+'######################################')

#engine = create_engine('sqlite:///'+dbname+'.db', echo=True)
engine = create_engine('sqlite:///user.db', echo=True)
Base = declarative_base()

class User(Base):
	__tablename__ = "user"
	username = Column(String, unique=True, primary_key=True)
	password = Column(String)

	def __init__(self, username, password):
		self.username = username
		self.password = password
#Base.metadata.create_all(engine)

class UserSchema(ma.Schema):
	class Meta:
		fields = ('username','password')

user_schema=UserSchema()
users_schema=UserSchema(many=true)

class Ride(Base):
	__tablename__ = "ride"
	rideId = Column(Integer, primary_key=True)	
	created_by = Column(String())
	timestamp = Column(String())
	source = Column(Integer)
	destination = Column(Integer)
	riders_list = Column(PickleType())



	def __init__(self, created_by, timestamp, source, destination, riders_list=[]):
		self.created_by = created_by
		self.timestamp = timestamp
		self.source = source
		self.destination = destination
		self.riders_list = riders_list


class RideSchema(ma.Schema):
	class Meta:
		fields = ('rideId','timestamp','created_by', 'source', 'destination', 'riders_list')




ride_schema = RideSchema()
rides_schema = RideSchema(many=True)

Base.metadata.create_all(engine)

#sudo rabbitmqctl list_queues...to list queues using rabbitmqctl tool
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rmq'))
channel = connection.channel()



#channel.queue_declare(queue='syncQ',durable=True)

def callback(ch, method, properties, body):
	Session=sessionmaker(bind=engine)
	session=Session()
	data=json.loads(body)

	if(data['method']=='POST'):
		if(data['table']=='User'):
			if(data['some']=='add_user'):
				username=data['username']
				password=data['password']
				new_user=User(username,password)
				session.add(new_user)
				session.commit()

			elif(data['some']=='remove_user'):
				user=data["username"]
				user = session.query(User).get(user)
				session.delete(user)
				session.commit()

			elif(data['some']=='clear_db'):
				session.query(User).delete()
				session.commit()

		elif(data['table']=='Ride'):
			if(data['some']=='add_ride'):
				username=data["created_by"]
				timestamp=data["timestamp"]
				source=data["source"]
				destination=data["destination"]	
				new_ride=Ride(username, timestamp, source, destination)
				session.add(new_ride)
				session.commit()

			elif(data['some']=='delete_ride'):
				ride1=data["rideId"]
				ride = session.query(Ride).get(ride1)
				session.delete(ride)
				session.commit()

			elif(data['some']=='join_ride'):
				user=data["username"]
				ride1=data["rideId"]
				ride = session.query(Ride).filter(Ride.rideId == ride1).first()
				l=ride.riders_list
				if user not in l:
					l.append(user)
					ride.riders_list=l
					flag_modified(ride,"riders_list")
					session.merge(ride)
					session.flush()
					session.commit()

			elif(data['some']=='clear_db'):
				session.query(Ride).delete()
				session.commit()

				
			else:
				column=data['column']
				value=data['value']
				username=data['username']
				user=session.query(User).get(username)
				user.password=value
				session.commit()
			
	###########################
	
def sync(ch,method,props,body):
	print(" in sync now")
	Session=sessionmaker(bind=engine)
	session=Session()
	data=json.loads(body)

	if(data['method']=='POST'):
		if(data['table']=='User'):
			if(data['some']=='add_user'):
				username=data['username']
				password=data['password']
				new_user=User(username,password)
				session.add(new_user)
				session.commit()

			elif(data['some']=='remove_user'):
				user=data["username"]
				user = session.query(User).get(user)
				session.delete(user)
				session.commit()

			elif(data['some']=='clear_db'):
				session.query(User).delete()
				session.commit()


		elif(data['table']=='Ride'):
			if(data['some']=='add_ride'):
				username=data["created_by"]
				timestamp=data["timestamp"]
				source=data["source"]
				destination=data["destination"]
				#riders_list=[]
				new_ride=Ride(username, timestamp, source, destination)
				session.add(new_ride)
				session.commit()

			elif(data['some']=='delete_ride'):
				ride1=data["rideId"]
				ride = session.query(Ride).get(ride1)
				session.delete(ride)
				session.commit()

			elif(data['some']=='join_ride'):
				user=data["username"]
				ride1=data["rideId"]
				ride = session.query(Ride).filter(Ride.rideId == ride1).first()
				l=ride.riders_list
				if user not in l:
					l.append(user)
					ride.riders_list=l
					flag_modified(ride,"riders_list")
					session.merge(ride)
					session.flush()
					session.commit()

			elif(data['some']=='clear_db'):
				session.query(Ride).delete()
				session.commit()

				
			else:
				column=data['column']
				value=data['value']
				username=data['username']
				user=session.query(User).get(username)
				user.password=value
				session.commit()


	'''
	print(" in sync now")
	Session = sessionmaker(bind=engine)
	session = Session()
	data=json.loads(body)
	u1 = User(data['user'],data['pw'])
	session.add(u1)
	session.commit()'''

def on_request(ch,method,props,body):
	Session = sessionmaker(bind=engine)
	session = Session()
	data = json.loads(body)

	table=data['table']
	if(table == 'User'):
		if(data['some']=='add_user'):
			username = data['username']
			existing_username = session.query(User).filter(User.username == username).all()
			response = users_schema.dump(existing_username)


		elif(data['some']=='list_user'):
			all_users = session.query(User).all()
			response = users_schema.dump(all_users)

		elif(data['some']=='remove_user'):
			username=data['username']
			existing_username=session.query(User).filter(User.username == username).all()
			response=users_schema.dump(existing_username)
			print(response)

	elif(data['table']=='Ride'):
		if(data['some']=='add_ride'):
			username=data["created_by"]
			existing_user = session.query(User).filter(User.username == username).all()
			response = rides_schema.dump(existing_user)

		elif(data['some']=='delete_ride'):
			ride1=data["rideId"]
			ride = session.query(Ride).filter(Ride.rideId == ride1).all()
			response = rides_schema.dump(ride)

		elif(data['some']=='join_ride'):
			ride1=data["rideId"]
			ride = session.query(Ride).filter(Ride.rideId == ride1).first()
			response = ride_schema.dump(ride)

		elif(data['some']=='ride_details'):
			ride1=data["rideId"]
			ride_detail = session.query(Ride).filter(Ride.rideId==ride1).all()
			response = rides_schema.dump(ride_detail)

		elif(data['some']=='upcoming_rides'):
			source=data["source"]
			destination=data["destination"]	
			ride2=session.query(Ride).filter(Ride.source==int(source),Ride.destination==int(destination)).all()
			sk=rides_schema.dump(ride2)
			#response2=rides_schema.dump(sk)
			print("this is sk")
			print(sk)
			upcoming=[]
			if(len(sk)==0):
				response = rides_schema.dump(sk)
			else:
				for i in range(len(sk)):
					#y = session.query(Ride).get(i)
					#print("this is y")
					#print(y)
					y=sk[i]
					tstamp=y["timestamp"]
					dt_value = datetime.strptime(tstamp, '%d-%m-%Y:%S-%M-%H')
					present_ts=datetime.utcnow()
					user1=y["created_by"]
					print("username")
					print(user1)
					ucheck = session.query(User).filter(User.username == user1).first()
					if(str(ucheck)=="None"):
						pass
					elif(dt_value>present_ts):
						lol={}
						lol["rideId"]=y["rideId"]
						lol["username"]=y["created_by"]
						lol["timestamp"]=y["timestamp"]
						upcoming.append(lol)
						print("this is upcoming ")
						print(upcoming)
						response = rides_schema.dump(upcoming)
						print("this is response")
						print(response)
			#response = {'data':res}
			
			#print(response)
	
	ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                         props.correlation_id),
                     body=json.dumps(response))
	ch.basic_ack(delivery_tag=method.delivery_tag)


logging.basicConfig()
zk = KazooClient(hosts='zoo:2181')
zk.start()

#sed = os.uname()[1]
#print(sed)

#client2=docker.DockerClient(base_url='unix:///var/run/docker.sock')
#client1=docker.APIClient(base_url='unix:///var/run/docker.sock')##
#client2=docker.DockerClient(base_url='tcp://192.168.0.21:2375')
# this = client2.containers.get(sed)

#this=client.containers.get(sed)
name1="master"
#name2="hithere"
#print(this.attrs["State"]["Pid"])

zk.ensure_path("/master")
zk.ensure_path("/slave")

#def delete_zoo():
#	global this
#	pid=str((this.attrs)["State"]["Pid"])
#	zk.delete("/slave/"+str(pid))
#	time.sleep(1)
#	this.stop()

#atexit.register(delete_zoo)
if(os.environ['WORKER'] == 'MASTER'):


#	zk.create("/master/"+str((this.attrs)["State"]["Pid"]),this.id.encode,ephemeral=True)
	zk.create("/master/"+name1,b"hello",ephemeral=True)
	print("master znode")
	channel.queue_declare(queue='writeQ', durable=True)
	channel.basic_consume(queue='writeQ', on_message_callback=callback,auto_ack=True)

	channel.start_consuming()

	

elif(os.environ['WORKER'] == 'SLAVE'):

	print("in slave")		
	#print(this.attrs["State"]["Pid"])
	zk.create("/slave/"+dbname,b"hey",ephemeral=True)
	Session=sessionmaker(bind=engine)
	session=Session()
	rs1=requests.post(url='http://18.233.36.130/get_db',json={'table':'User'})
	for item in rs1.json():
		u=User(item["username"],item["password"])
		session.add(u)
		session.commit()
	rs2=requests.post(url='http://18.233.36.130/get_db',json={'table':'Ride'})
	for item in rs2.json():
		u=Ride(item["created_by"],item["timestamp"],item["source"],item["destination"])
		session.add(u)
		session.commit()
	channel.queue_declare(queue='task_queue', durable=True)
	channel.basic_qos(prefetch_count=1)
	channel.basic_consume(queue='task_queue', on_message_callback=on_request)


	channel.exchange_declare(exchange = 'syncQ',exchange_type = 'fanout')
	result = channel.queue_declare(queue='',exclusive=True)
	queue_name = result.method.queue
	channel.queue_bind(exchange='syncQ', queue=queue_name)
	channel.basic_consume(queue=queue_name, on_message_callback=sync, auto_ack=True)
	print(" [x] Awaiting RPC requests")
	channel.start_consuming()
else:
	print("no worker variable set")



#!/usr/bin/python
from flask import Flask, request, jsonify, abort, Response
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from requests.exceptions import HTTPError
from flask_track_usage import TrackUsage
from flask_track_usage.storage.sql import SQLStorage
from apscheduler.schedulers.background import BackgroundScheduler


import os
import json
import string
import requests
import datetime
import time
import pika
import sys
import uuid
import docker
import time
import math
import atexit
import threading
import logging

from kazoo.client import KazooClient
from kazoo.client import KazooState

logging.basicConfig()
zk = KazooClient(hosts='zoo:2181')
zk.start()

#sed = os.uname()[1]
print("hi")


client=docker.DockerClient(base_url='unix:///var/run/docker.sock')
client1=docker.APIClient(base_url='unix:///var/run/docker.sock')
#client=docker.DockerClient(base_url='198.162.0.21:2375')
#client1=docker.APIClient(base_url='198.162.0.21:2375')
#this = client.containers.get(sed)



app = Flask(__name__)

class read(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rmq'))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, message):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='task_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=json.dumps(message))
        while self.response is None:
            self.connection.process_data_events()
        return (self.response)

class write(object):
	def __init__(self):
		self.connection = pika.BlockingConnection(
            		pika.ConnectionParameters(host='rmq'))

		self.channel = self.connection.channel()
		self.channel.queue_declare(queue='writeQ',durable=True)
	def call(self,message):
		self.channel.basic_publish(
        		exchange='',
        		routing_key='writeQ',
        		body=json.dumps(message),
        		properties=pika.BasicProperties(
            		delivery_mode=2,  # make message persistent

        		))

class sync(object):
    def __init__(self):
        self.connection = pika.BlockingConnection(
            		pika.ConnectionParameters(host='rmq'))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange = 'syncQ',exchange_type = 'fanout')

    def call(self,message):
        self.channel.basic_publish(
            exchange='syncQ',
            routing_key='',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ))






global no_slaves
no_slaves=1


def slave_watcher(event):
    #duplicate database
#	master = client.containers.get(zk.get("/master/"+zk.get_children("/master")[0])[0].decode())
#	master.commit('worker:latest')
	slave = client.containers.run(
		privileged=True,
		image = 'worker:latest',
		network='orch_default',
		links={'rmq':'rmq','zoo':'zoo'},
		command = 'sh -c "sleep 20 && python3 worker.py"',
		environment = {'WORKER':'SLAVE'},
		detach=True
	)
        
	return 1


def job_function():
	currentDT = datetime.datetime.now()
	
	global counter
	global no_slaves
	temp = counter
	if( no_slaves == 1 and temp>=20):
		print("scaling up")
		cont = client.containers.run(
				privileged=True,
				image = 'worker:latest',
				command = 'sh -c "sleep 20 && python3 worker.py"',
				environment = {'WORKER':'SLAVE'},
				links={'rabbitmq':'rmq','zookeeper':'zoo'},
				network='orch_default',
				detach=True
				)
			
		no_slaves = no_slaves+1

	elif(no_slaves ==2 and temp <20):
		print("scaling down")
		cont_pid=[]
		for container in client.containers.list():
		
			if(container.name != 'orchestrator' and container.name != 'zookeeper' and container.name != 'rabbitmq' and container.name != 'master'):
				d={}
				d['0']=container.id
				d['1']=container.attrs['State']['Pid']
				cont_pid.append(d)

		sorted_list=sorted(cont_pid,key = lambda x:x['1'],reverse=True)
		max_id = sorted_list[0]['0']
		client1.kill(max_id)
		cont_pid.remove(sorted_list[0])
			
		no_slaves=no_slaves-1


	counter = 0



print("CREATING CONTAINER 2 - SLAVE")
container2 = client.containers.run(
		privileged=True,
		image = 'worker:latest',
		name = 'slave1',
		command = 'sh -c "sleep 20 && python3 worker.py"',
		environment = {'WORKER':'SLAVE'},
		links={'rabbitmq':'rmq','zookeeper':'zoo'},
		network='orch_default',
		detach=True
        )



global ride
global user
ride=[]
user=[]

@app.route("/api/v1/db/write", methods=["POST","DELETE"])#write api
def write_to_db():
   
    print("write to db") 
    message=request.get_json()
    message['method']=request.method
    if(message['some']=='add_user' or message['some']=='add_ride'):
        if(message['table']=='User'):
            user.append(message)
        else:
            ride.append(message)	

    instance=write()
    instance.call(message)

    instance1=sync()
    instance1.call(message)
    
    print(" [x] Sent %r" % message)
    return {"status":"done"}

global counter
counter=0
global flag
flag=True

@app.route("/api/v1/db/read",methods=["POST"])
def read_from_db():
	global counter
	global flag
	counter = counter+1
	if(counter == 1 and flag):
		sched = BackgroundScheduler(daemon=True)
		sched.add_job(job_function,'interval',minutes=2)
		sched.start()
		flag = False
	print("write to db") 
	message = request.get_json()
	print(message)
	instance=read()
	response = instance.call(message)
	print("waiting for message")
	print("[.] Got %r" % response)
	data = json.loads(response)
	return jsonify(data)


@app.route("/get_db",methods=["POST"])
def get_db():
        s=request.get_json()
        if(s['table']=='User'):
            return jsonify(user)
        else:
            return jsonify(ride)

@app.route("/api/v1/worker/list",methods=["GET"])
def list_workers():
	cont_pid=[]
	for container in client.containers.list():
		if(container.name != 'orchestrator' and container.name !='zookeeper' and container.name !='rabbitmq'):
			cont_pid.append(container.attrs['State']['Pid'])
	cont_pid.sort()
	print(cont_pid)
	return jsonify(cont_pid)

@app.route("/api/v1/crash/slave",methods=["POST"])
def crash_slave():
	slave_list=zk.get_children("/slave",watch=slave_watcher)
	cont_pid=[]
	for container in client.containers.list():
		
		if(container.name != 'orchestrator' and container.name != 'zookeeper' and container.name != 'rabbitmq' and container.name != 'master'):
			d={}
			d['0']=container.id
			d['1']=container.attrs['State']['Pid']
			cont_pid.append(d)

	sorted_list=sorted(cont_pid,key = lambda x:x['1'],reverse=True)
	max_id = sorted_list[0]['0']
	client1.kill(max_id)
	cont_pid.remove(sorted_list[0])
	l=[]
	l.append(sorted_list[0]['1'])
	return jsonify(l),200




app.run(debug=True, host='0.0.0.0', port=80, threaded=True, use_reloader=False)
#app.run(debug=False)

FIRST ASSIGNMENT:
In the assigment 1 we have implemented the backend processing of ​RideShare using REST APIs on the AWS instance. Firstly we have implemented rest APIs using Flask framework then we integrated Flask with databases through Flask SQLAlchemy. We later deployed it on EC2 instance using Apache server. 
The following are the list of APIs:
1. Add user
2. Remove user
3. Create a new ride
4. List all upcoming rides for a given source and destination.
5. List all details of a given ride
6. Join an existing ride
7. Delete a ride
8. Write to db

COMMANDS:
python app.py

-----------------------------------------------------

SECOND ASSIGNMENT:
In the assignment 2 we have created two different microservices for users and rides in seperate docker containers running on one AWS instance. We created an instance and added port 80 then we made it’s ip elastic. Later in the instance we have created two containers each for users and rides file along with their requirements, docker-compose.ymland dockerfile respectively and then we ran the below command which created communication between the two containers and then we ran APIs in postman with the elastic ip of the instance in the API.
In this assignment we have created list all users API for users and clear db API for both users and rides along with the APIS that we built in first assignment.


COMMANDS:
sudo docker-compose up - - build

-----------------------------------------------------


THIRD ASSIGNMENT:
In the assignment 3 we have created two different microservices into two different AWS EC2 instances. We have created two instances with port 80 and target group for each, then the ip of the instance were made elastic. Then we created a load balancer that supports path based routing and AWS application load balancer will distribute incoming http request based on URL of the request, so that all the user APIs are forwarded to the user instance and ride APIs to the ride instance except the the count API and clear dB API which are called by the public api of each microservices directly. Each container will run by using the below command and the APIs are run in the postman with the load balancer DNS name in all API except clearing and count_no_of_request.
In this assignment we have added get total HTTP requests made to miceroservices API and reset HTTP requests counter API along with the APIS that we built in first and second assignments.

COMMANDS: 
sudo docker-compose up - - build 
(on both instances)

-----------------------------------------------------

FINAL PROJECT:
In the final project we had built a fault tolerant, highly available database as a service for RideShare application. We have created three different microservices for users, rides and one for Orchestrator. We had built a load balancer for users and rides instance.
We implemented custom database orchestrator engine that will listen to incoming http request 
from users and rides microservices and perform the database read and write operation according to the given specifications. The ip of orchestrator instance is also made elastic.
We have used Advanced Message Queue Protocol using RabitMQ as a message broker for our assignment. Now the load balancer accepts the requests and pass them to the respective instance in addition to the dB read/write are exposed to the orchestrator which uses the RabbitMQ queues to send all the write requests to the master and the read request to the slaves using writeQ and readQ respectively, syncQ is used to update the database.

High Availability:
We are using zoo keeper to watch on each worker.
When a slave worker fails and new slave worker is started and data is copied asynchronously, using crash/slave api another slave will be started.

Scalability:
After every two minutes depending on the number of requests received the orchestrator will increase/decrease the number of slave worker containers.
We are running 5 containers in the database instance those are Orchestrator, RabbitMQ, Zookeeper, master, and slave. All the containers will run by using the below command.
In this Project we have also implemented two more APIs, one API is called to kill the slave whose container's pid is highest and when other API is called the response should be sorted list of container's pid of all the workers.

COMMANDS:
sudo docker-comopse up - - build 
(on all three instances)






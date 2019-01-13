#!/bin/bash

#update apt
sudo apt-get -y update

#install docker
sudo apt-get -y remove docker docker-engine docker.io
sudo apt-get -y update
sudo apt-get -y install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo apt-key fingerprint 0EBFCD88
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get -y update
sudo apt-get -y install docker-ce

#Reset previous install
sudo sh Reset.sh

#create docker network
sudo docker network create -d bridge --subnet 10.10.10.0/24 RainMakerNetwork

#create WebRole image and container
sudo docker build -t flask-webrole:latest ./WebRole/
sudo docker run --network=RainMakerNetwork --ip=10.10.10.2 --name=WebRole -d -p 9000:80 flask-webrole

#create WorkerRole image and container
sudo docker build -t flask-workerrole:latest ./WorkerRole/
sudo docker run --network=RainMakerNetwork --ip=10.10.10.3 --name=WorkerRole -d -p 9001:80 flask-workerrole

#display created containers
sudo docker ps -a

echo "Setup Complete\n"
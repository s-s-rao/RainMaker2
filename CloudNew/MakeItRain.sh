#!/bin/bash

#update apt
# sudo apt-get -y update

#install docker
# sudo apt-get -y remove docker docker-engine docker.io
# sudo apt-get -y update
# sudo apt-get -y install apt-transport-https ca-certificates curl software-properties-common
# curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
# sudo apt-key fingerprint 0EBFCD88
# sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
# sudo apt-get -y update
# sudo apt-get -y install docker-ce

#Reset previous install
sudo sh Reset.sh

#initialize
# sudo apt-get -y install python3-pip
# sudo apt-get -y install mysql-client
# pip3 install pymysql
python3 ./Files/Init.py

#display docker network
docker network ls

echo "\n"

#display created containers
docker ps -a
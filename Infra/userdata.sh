#!/bin/bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose git

git clone https://github.com/Sahilpatkar/Health_Tracker_Python /home/ubuntu/app

cd /home/ubuntu/app
docker-compose up -d
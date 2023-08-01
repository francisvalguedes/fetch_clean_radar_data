#!/bin/bash
sudo apt install -y python3-pip
sudo apt install -y gfortran
sudo apt install -y cmake
sudo apt install -y python3-venv
python -m venv .env
# pip install virtualenv
# sudo apt install python3 virtualenv

# virtualenv env
source env/bin/activate
pip install -r requirements.txt
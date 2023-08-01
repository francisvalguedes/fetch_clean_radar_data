# Fetch and Clean Radar Data

## Instalar dependências sem criar ambiente virtual:

~~~
sudo apt install -y python3
sudo apt install -y python3-pip

pip install -r requirements.txt
~~~

## Instalar dependências com ambiente virtual:

~~~
sudo apt install -y python3
sudo apt install -y python3-pip
sudo apt install -y python3-venv
python -m venv .env

source env/bin/activate
pip install -r requirements.txt
~~~

## Utilização;

Colocar os arquivos brutos .d na pasta raw_data/

Executar python fech_preprocess_data.py

Os arquivos resultantes aparecem nas pastas raw_data_split/ e clear_data/
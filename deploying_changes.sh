#!/bin/bash

echo '[-------------] Start deploying changes...'

cd /home/code/rating
echo "[-------------] Target folder: $(pwd)"

# pull the changes
echo "[-------------] Git pull..."
git pull

cd /home/code
echo "[-------------] Target folder: $(pwd)"

# check & activate env
if [ -d /home/code/env ]; then
    echo '[-------------] Venv exists!'
    . ./env/bin/activate
else
    echo '[-------------] Creating Venv...'
    python3 -m venv env
fi

cd /home/code/rating
echo "[-------------] Target folder: $(pwd)"

sed -i "/psycopg2==2.9.3/d" requirements.txt

# install requirements
echo "[-------------] Install dependencies..."
pip install -r requirements.txt

# cd to root project
cd /home/code/rating/rating
echo "[-------------] Target folder: $(pwd)"

# makemigrations and migrate
echo "[-------------] Make migrations and migrate..."
python manage.py makemigrations
python manage.py migrate

# collectstatic
echo "[-------------] Collect staticfiles..."
manage.py collectstatic --noinput

echo "[-------------] Deactivate venv..."
deactivate

# restart gunicorn and reload nginx
echo "[-------------] Restart Gunicorn & NGINX..."
sudo systemctl restart gunicorn
sudo systemctl reload nginx

echo "[-------------] Finish!"

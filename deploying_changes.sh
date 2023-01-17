#!/bin/bash

echo '[-------------] Start deploying changes...'

cd /home/code/rating
echo "[-------------] Target folder: $(pwd)"

echo "[-------------] Local changes: $(git status)"

# discharge local changes
echo "[-------------] Git clean local changes..."
git clean -f
echo "[-------------] Local changes after clean: $(git status)"

# pull the changes
echo "[-------------] Git pull..."
git pull

cd /home/code
echo "[-------------] Target folder: $(pwd)"

# check & activate env
if [ -d /home/code/env ]; then
    echo '[-------------] VENV exists!'
    . ./env/bin/activate
    if [ $? -ne 0 ]; then
        echo "[----------!!!] VENV don't activated!"
        exit 1
    else
        echo "[++++++++++++] VENV activated"
    fi

else
    echo '[-------------] Creating VENV...'
    python3 -m venv env
fi

cd /home/code/rating/rating
echo "[-------------] Target folder: $(pwd)"

sed -i "/psycopg2==2.9.3/d" requirements.txt

# install requirements
echo "[-------------] Install dependencies..."
pip install -r requirements.txt

# cd to root project
cd /home/code/rating/rating
echo "[-------------] Target folder: $(pwd)"

# makemigrations
echo "[-------------] Make migrations..."
python manage.py makemigrations

# migrate
echo "[-------------] Migrate..."
python manage.py migrate

# collectstatic
echo "[-------------] Collect staticfiles..."
python manage.py collectstatic --noinput

echo "[-------------] Deactivate venv..."
deactivate

# restart gunicorn and reload nginx
echo "[-------------] Restart Gunicorn & NGINX..."
sudo systemctl restart gunicorn
sudo systemctl reload nginx
echo "[-------------] Finish!"

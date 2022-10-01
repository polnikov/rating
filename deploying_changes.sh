#!/bin/bash

echo 'Start deploying changes...'

cd /home/code/rating
echo "Target folder: $(pwd)"

# pull the changes
echo "Git pull..."
git pull

cd /home/code
# check & activate env
if [[ -d "env" ]]; then
    echo 'Venv exists...'
    . ./env/bin/activate
else
    echo 'Creating Venv...'
    python3 -m venv env
fi

cd /home/code/rating
sed -i "/psycopg2==2.9.3/d" requirements.txt

# install requirements
echo "Install dependencies..."
pip install -r requirements.txt

# cd to root project
cd /home/code/rating/rating

# makemigrations and migrate
echo "Make migrations and migrate..."
python manage.py makemigrations
python manage.py migrate

# collectstatic
echo "Collect staticfiles..."
manage.py collectstatic --noinput

deactivate

# restart gunicorn and reload nginx
echo "Restart Gunicorn & NGINX..."
sudo systemctl restart gunicorn
sudo systemctl reload nginx

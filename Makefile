
setup:
	apt-get install python3-pip -y
	pip3 install --upgrade pip

build:
	pip3 install -r requirements.txt
	export FLASK_APP=app.py
	echo "flask build steps should be used for production deployment!"
	flask user check

run:
	ls -R
# 	gunicorn -w 4 -b 0.0.0.0:5000 app:app
	flask run --host=0.0.0.0 --cert adhoc

dockertest:
	make setup
	make build
	make run


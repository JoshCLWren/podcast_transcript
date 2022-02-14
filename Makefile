venv:
	pyenv install 3.8.7 --skip-existing
	-pyenv uninstall -f transcript
	-pyenv virtualenv 3.8.7 transcript
	pyenv local transcript
	pip install --upgrade pip
	pip install --upgrade pip-tools

deps-install:
	python -m pip install --upgrade pip
	pip install --upgrade -r requirements.txt

server:
	watchmedo auto-restart -p "*.py" -R python -- app.py

heroku:
	heroku local

deps-compile:
	pip install --upgrade pip-tools
	pip-compile requirements.in

deps-update:
	python -m pip install --upgrade pip
	pip install --upgrade pip-tools
	pip-compile requirements.in
	pip install --upgrade -r requirements.txt

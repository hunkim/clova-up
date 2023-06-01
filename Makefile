VENV = .venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip3
UVICORN = $(VENV)/bin/uvicorn

include .env
export

# Need to use python 3.9 for aws lambda
$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt

init: $(VENV)/bin/activate

app: init
	$(PYTHON) clova_up.py reload

clova: init
	$(PYTHON) clova_util.py

clean:
	rm -rf __pycache__
	rm -rf $(VENV)

# book

Web app for booking inspired by [Doodle](https://doodle.com/en/) and [Framadate](https://framadate.org/abc/en/). Deployed at https://thepanoply.eu.pythonanywhere.com/.

## Installation

Setup a virtual environment and install the dependencies:
```bash
python3.8 -m virtualenv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r src/requirements-dev.txt
```

## Development server

Run the development server with password `1234` and debug mode:
```bash
bash start_flask.sh
```
NOTE: For development only. Do not run this in production...

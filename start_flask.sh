#!/bin/bash

export FLASK_APP=app
export FLASK_ENV=development
export PASSWORD=1234

flask run --debug #--host=0.0.0.0 # Uncomment to xperiment on local network

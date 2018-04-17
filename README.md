# ABE

Amorphous Blob of Events

## Getting Started

### MongoDB

Install MongoDB. Use [these
instructions](https://docs.mongodb.com/getting-started/shell/installation/). On
macOS with [Homebrew](https://brew.sh/) installed, you can instead run `brew install mongodb`.

### Setup Python Virtual Environment

```shell
pip3 install virtualenv  # install the virtual environment package
virtualenv -p python3 venv  # create a virtual environment in the `venv` folder
```

**All python commands should be run from within the virtual environment.**
To activate the virtual environment, run

```shell
source ./venv/bin/activate  # activate the virtual environment for the current shell
```

You should now notice `(venv)` prepending your command prompt.
This signifies that you are working within the virtual environment. This only applies to your current shell instance, so you'll need to run it every time you open a new terminal window you'd like to use it in.

If you'd like to exit the virtual environment, run

```shell
deactivate  # deactivates the virtual environment
```

### Install Requirements

```shell
pip install -r requirements.txt  # install the required packages for the project
```

### Setup mongo_config.py

In order to connect to a mongodb instance other than your localhost, you can create a copy of [`mongo_config_sample.py`](abe/mongo_config_sample.py) called `mongo_config.py`. This configuration file is gitignored and can specify a uri for mongodb to connect to.

### Run ABE

To start a local version of ABE, run

```shell
python run.py
```

### Load Sample Data

To load [sample data](abe/sample_data.py) into the database, run

```shell
python -m abe.sample_data
```

## Development

### Running the API server

Run `python run.py`

Visit <http://127.0.0.1:3000>. You should see a top hat.

Visit <http://127.0.0.1:3000/events/>. You should see `[]`. (This is an empty
JSON list of events.)

### Testing

`python -m unittest`

This is noisy, but should print `OK` at the end:

```bash
$ python -m unittest
…
----------------------------------------------------------------------
Ran 4 tests in 1.124s

OK
```

## Configuration


| Name        | Default | Description                   |
|-------------|---------|-------------------------------|
| FLASK_DEBUG | False   | Flask debug mode              |
| PORT        | 3000    | HTTP(S) port                  |
| REQUIRE_SSL | False   | Use HSTS to redirect to HTTPS |

## API Documentation

### abe.olin.build/events/

| HTTP Method | Action              |
| ----------- | ------------------- |
| GET         | retrieve all events |
| POST        | create new event    |

### abe.olin.build/events/24

| HTTP Method | Action                    |
| ----------- | ------------------------- |
| GET         | retrieve event with id 24 |
| PUT         | update event with id 24   |
| DELETE      | delete event with id 24   |

### abe.olin.build/events/ShortScarletFrog

| HTTP Method | Action                                    |
| ----------- | ----------------------------------------- |
| GET         | retrieve event with id "ShortScarletFrog" |
| PUT         | update event with id "ShortScarletFrog"   |
| DELETE      | delete event with id "ShortScarletFrog"   |

### abe.olin.build/labels/

| HTTP Method | Action              |
| ----------- | ------------------- |
| GET         | retrieve all labels |
| PUT         | create new label    |

### abe.olin.build/labels/clubs

| HTTP Method | Action                           |
| ----------- | -------------------------------- |
| GET         | retrieve label with name "clubs" |
| PUT         | update label with name "clubs"   |
| DELETE      | delete label with name "clubs"   |

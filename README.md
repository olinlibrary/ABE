# ABE
Amorphous Blob of Events

## Getting Started

### MongoDB

- [installation instructions](https://docs.mongodb.com/getting-started/shell/installation/)

### Python

#### Setup Virtual Environment

```shell
sudo pip3 install virtualenv
virtualenv -p python3 venv
source ./venv/bin/activate
```

#### Install Requirements

```shell
pip install -r requirements.txt
```

#### mongo_config.py

In order to connect to a mongodb instance other than your localhost, you can create a copy of [`mongo_config_sample.py`](mongo_config_sample.py) called `mongo_config.py`. This configuration file is gitignored and can specify a uri for mongodb to connect to.

## API

<<<<<<< HEAD
### abe.olin.build/events
=======
### abe.olin.build/events/
>>>>>>> dev

| HTTP Method | Action |
| ------------- | ------------- |
| GET | retrieve all events |
| POST | create new event |

### abe.olin.build/events/24

| HTTP Method | Action |
| ------------- | ------------- |
| GET | retrieve event with id 24 |
| PUT | update event with id 24 |
| PATCH | partially update event with id 24 |
| DELETE | delete event with id 24 |

### abe.olin.build/events/ShortScarletFrog

| HTTP Method | Action |
| ------------- | ------------- |
| GET | retrieve event with id "ShortScarletFrog" |
| PUT | update event with id "ShortScarletFrog" |
| PATCH | partially update event with id "ShortScarletFrog" |
| DELETE | delete event with id "ShortScarletFrog" |

<<<<<<< HEAD
### abe.olin.build/labels
=======
### abe.olin.build/labels/
>>>>>>> dev

| HTTP Method | Action |
| ------------- | ------------- |
| GET | retrieve all labels |
| PUT | create new label |

### abe.olin.build/labels/clubs

| HTTP Method | Action |
| ------------- | ------------- |
| GET | retrieve label with name "clubs" |
| PUT | update label with name "clubs" |
| PATCH | partially update label with name "clubs" |
| DELETE | delete label with name "clubs" |

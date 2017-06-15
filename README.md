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

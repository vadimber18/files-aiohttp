Files app
===========


Apps
---------

files
^^^^^^^

* contains 6 API handlers (`register`, `login`, `files`, `files_detail`, `files_upload`, `files_download_detail`)
* API: logged-in users can both upload and download files, unauthorized users can register, login and get files/files_details


Features
---------

auth_middleware
^^^^^^^^^^^^^^^

Upload/download API handlers processed by `auth_middleware` - simple jwt token implementation described in `middlewares.py`

aiohttp-admin
^^^^^^^^^^^^^

Simple `aiohttp-admin` for user and file models

swagger
^^^^^^^

Each API endpoint described. loads from .json file.

docker
^^^^^^

There are two docker configurations - `local.yml` and `production.yml`. production one uses nginx web-server to serve file uploads and main app


tests
^^^^^

App contains tests for API handlers using aiohttp-pytest. some of them load data from json-fixtures

Installation
------------

* `docker-compose -f production.yml build`
* `docker-compose -f production.yml up`
* to run tests: `docker-compose -f local.yml run aio pytest tests`
* `swagger` available on `127.0.0.1:8000`, but you can always use Insomnia or such thing to test API.
* `aiohttp-admin` available on `127.0.0.1/admin` `user:admin password:admin_pass`
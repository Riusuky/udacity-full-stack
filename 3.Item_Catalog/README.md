# Item Catalog
This project consists of an item catalog application. It allows logged users to create items that belongs to user defined categories. Items have a name and a category associated, and they may also contain an image and a description.

## Requirements

For these first 4 requirements, I used [Vagrant](https://www.vagrantup.com/) and [this vagrant configuration file](https://github.com/udacity/fullstack-nanodegree-vm/blob/master/vagrant/Vagrantfile) to set up a virtual machine and install these requirements.

* [PostgreSQL](https://www.postgresql.org/) database server;
* [SQLAlchemy](http://www.sqlalchemy.org/) library;
* [Flask](http://flask.pocoo.org/) framework;
* [Redis](https://redis.io/);

You also need these following requirements:

* [Flask-Uploads](http://pythonhosted.org/Flask-Uploads/#flaskext.uploads.configure_uploads) (You may install it using `sudo pip3 install Flask-Uploads`);
* [Psycopg](https://wiki.postgresql.org/wiki/Psycopg2), a PostgreSQL database adapter for the Python (You may install it using `sudo pip3 install psycopg2`)
* [Google APIs Client](https://developers.google.com/api-client-library/python/start/installation) library for Python (You may install it by using `sudo pip3 install --upgrade google-api-python-client`);

## Getting Started

After installing all the requirements, create the `udacity_catalog` database used for this application. You can achieve this by first connecting to the database server using `psql` and then using `CREATE DATABASE udacity_catalog`.

Before running the application, first start the Redis server using `redis-server` on a terminal. Then, in another terminal, run the `view.py` script using `python3 view.py` (make sure that your current directory is set to the parent of the `view.py` file) to run the application.

Access the application on your browser at the URI `http://localhost:5000/`.

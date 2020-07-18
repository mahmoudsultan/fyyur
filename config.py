import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database


# DATABASE URL: Current URI is a Shortcut for me if necessary replace to add <username>:<password> part
SQLALCHEMY_DATABASE_URI = 'postgres:///fyyur'
SQLALCHEMY_TRACK_MODIFICATIONS = False

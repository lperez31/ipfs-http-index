# IPFS + apache + ftp with docker-compose

## Work in Progress!

This work is in progress. It is not production ready.

## What is it?

This project bundles in docker-compose:

* An IPFS server
* A http server
* A ftp server
* A python script

The purpose is to serve a directory through IPFS, and maintaining a json file which describes the content of the directory.

## How does it work?

1. Send files via ftp in a directory
2. The python script scans the content of the directory every minute and creates a json file describing the content

The json file is served via http. You can view it at:

http://[IP_OF_YOUR_SERVER]/index.json

The json file contains the names of every file and the IPFS hash.

## Installation 

* Clone this repository
* cd to this project directory
* Execute setup.sh
* In docker-compose.yml, change PUBLICHOST value to your server domain name or IP
* Execute "docker-compose up"
* Create ftp user:
  * In another terminal, cd to this project directory, and get into the ftp container with this command: docker-compose exec pureftpd bash
  * Create the database: pure-pw mkdb
  * Create ftp user: pure-pw useradd REPLACE_BY_YOUR_USER_NAME -m -u ftpuser -d /home/ftpuser
  * Exit: exit

That's all. You should be able to:

* Connect by ftp with the user you have just created
* Send files
* See a index.json file with your browser
* Get the files with IPFS

For more info on pureftpd commands:



## Licence

Copyright Lior Perez 2017 - MIT licence
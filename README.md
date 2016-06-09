# Hedwig Client

Hedwig client is a simple python app, that is to be invoked via logstash on arrival of new email.
The python script will 
 1. Unzip the attachment file to a temp location (configurable via the config file)
 2. Read each file 
 3. Post each files content to the hedwig webapp
 
 
## Pre-requisites for the script
Please ensure the following python modules are installed and available on the system running hedwig client
1. requests

7z application needs to be installed and configured. Path has to be set in the config file

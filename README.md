# Hedwig Client

Hedwig client is a simple python app, that is to be invoked via logstash on arrival of new email.
The python script will 
 1. Unzip the attachment file to a temp location (configurable via the config file)
 2. Read each file 
 3. Post each files content to the hedwig webapp
 
 
### Pre-requisites for the script
Please ensure the following python modules are installed and available on the system running hedwig client
1. requests
2. email

### Pre-requisites for the client machine

1. Install and configure logstash
2. Update `path` in the hedwig-logstash.conf to point to the mail directory to be watched
3. Update `command` to point to the `asup_client.py` (`hedwig.cfg` location has to be updated accordingly)
4. Start logstash with the file `hedwig-logstash.conf`
5. 7z application needs to be installed and configured. Path has to be set in the config file

Note: 
* On mac 7z can be install from brew with `brew install p7zip` and 
it gets installed as a 7z executable under `/usr/loca/bin`. 
* On centos please follow this guide: http://ask.xmodulo.com/install-7zip-linux.html.
It gets installed as 7za under `/bin/7za`
* On Ubuntu do `apt-get install p7zip-full`



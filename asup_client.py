import requests
import ConfigParser
import email
import time
from requests.auth import HTTPBasicAuth
import sys

from utils import Utils
import shutil
from ast import literal_eval

class ASUP_Client():
    def __init__(self):
        config = ConfigParser.RawConfigParser()
        configFilePath = r'hedwig.cfg'
        config.read(configFilePath)
        self.appConf = config
        self.alertName = str(time.time())
        self.tempDir = self.appConf.get('hedwig', 'tmp.alerts.storage.path') + self.alertName + "/"
        self.required_files = set(literal_eval(self.appConf.get('hedwig', 'required.files')))
        self.user = self.appConf.get('hedwig', 'username')
        self.passwd = self.appConf.get('hedwig', 'password')

    def post_required_files(self, parsed_email):
        header = {'Accept': 'application/json', "Content-Type": "application/json"}
        alerts_url = self.appConf.get('hedwig', 'alerts.api.endpoint')
        #print 'Posting %s to %s' % (self.email_fields, alerts_url)
        respose =  requests.post(alerts_url, json=parsed_email, auth=HTTPBasicAuth(self.user, self.passwd), headers=header)
        #jr = json.loads(respose.text())
        #print(respose.json())
        self.alert_id = respose.json()['id']
        print "Posted required files with id: %s" % self.alert_id

    def post_all_files(self, all_files_data):
        header = {'Accept': 'application/json', "Content-Type": "application/json"}
        alerts_url = self.appConf.get('hedwig', 'all.alerts.api.endpoint')
        for file_name, file_data in all_files_data.iteritems():
            json_data = {}
            json_data['asup_alert_id'] = self.alert_id
            json_data['asup_alert_file_name'] = file_name
            json_data['asup_alert_file_data'] = str(file_data)
            respose = requests.post(alerts_url, json=json_data, auth=HTTPBasicAuth(self.user, self.passwd), headers=header)
            print "Posted file: %s with id: %s" % (file_name, respose.json()['id'])

    def get_alerts(self):
        alertsEndpoint = self.appConf.get('hedwig', 'alerts.api.endpoint')
        r = requests.get(alertsEndpoint, auth=HTTPBasicAuth(self.appConf.get('hedwig', 'username'), self.appConf.get('hedwig', 'password')))
        print(r.json())

    def parse_email(self, emailFile):
        # TODO validate email_file really exists
        print 'About to parse %s' % emailFile
        attachment_name = ""
        emailf = open(emailFile, 'rb')
        parsedEmail = email.message_from_file(emailf)
        email_fields = {}

        if len(parsedEmail) == 0:
            print 'Failed to parse email at %s' % emailFile
            return
        if parsedEmail.is_multipart():
            for payload in parsedEmail.get_payload():
                ctype = payload.get_content_type()
                #print ctype
                if ctype in ['text/plain']:
                    #print 'Body >>>>>>>>>' + payload.get_payload()
                    email_fields = utils.parse_email_body(str(payload.get_payload()))
                    print 'Finished parsing email body'
                elif ctype in ['application/octet-stream', 'application/x-7z-compressed']:
                    # This the attachment
                    attachment_name = "/tmp/" + self.alertName + payload.get_filename()
                    open(attachment_name, 'wb').write(payload.get_payload(decode=True))
                    print 'Finished writing attachment file at: %s' % attachment_name
                else :
                    print 'Unknown ctype: %s' % ctype
        else:
            print "Not a multi part email not sure how to process this"
        utils.unzip_attachment(attachment_name, self.tempDir)
        required_files, all_files = Utils.parse_alert_data(self.tempDir, self.required_files)
        email_fields['alerts'] = str(required_files)
        utils.cleanup(self.tempDir)
        return email_fields, all_files


alerts = ASUP_Client()
utils = Utils()
required_files_data, all_files_data = alerts.parse_email(sys.argv[1])
alerts.post_required_files(required_files_data)
alerts.post_all_files(all_files_data)
#alerts.test_required_files()


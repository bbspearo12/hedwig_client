import requests
import ConfigParser
import email
import time
import subprocess
from requests.auth import HTTPBasicAuth
import sys


class Alerts():

    def __init__(self):
        config = ConfigParser.RawConfigParser()
        configFilePath = r'hedwig.cfg'
        config.read(configFilePath)
        self.appConf = config
        self.alertName = str(time.time())
        self.tempDir = self.appConf.get('hedwig', 'tmp.alerts.storage.path') + self.alertName + "/"

    def post_alerts(self):
        header = {'Accept': 'application/json', "Content-Type": "application/json"}
        alerts_url = self.appConf.get('hedwig', 'alerts.api.endpoint')
        print 'Posting %s to %s' % (self.email_fields, alerts_url)
        respose =  requests.post(alerts_url, json=self.email_fields, auth=HTTPBasicAuth(self.appConf.get('hedwig', 'username'), self.appConf.get('hedwig', 'password')), headers=header)
        #jr = json.loads(respose.text())
        print(respose.json())
        self.alert_id = respose.json()['id']
        print self.alert_id

    def get_alerts(self):
        alertsEndpoint = self.appConf.get('hedwig', 'alerts.api.endpoint')
        r = requests.get(alertsEndpoint, auth=HTTPBasicAuth(self.appConf.get('hedwig', 'username'), self.appConf.get('hedwig', 'password')))
        print(r.json())

    def unzip_attachment(self, attachmentPath):
        # TODO validate attachmentPath exists
        print("Will unzip: "+ attachmentPath)
        sevenz = self.appConf.get('hedwig', '7z')
        decompress = subprocess.check_output([sevenz, 'x', "-o" + self.tempDir, attachmentPath])
        print("Decompressed: "+attachmentPath+" to location: "+ self.tempDir+", output is: "+decompress)

    def parse_email(self, emailFile):
        # TODO validate email_file really exists
        print 'About to parse %s' % emailFile
        attachment_name = ""
        emailf = open(emailFile, 'rb')
        parsedEmail = email.message_from_file(emailf)
        if len(parsedEmail) == 0:
            print 'Failed to parse email at %s' % emailFile
            return
        emailf.close()
        if parsedEmail.is_multipart():
            for payload in parsedEmail.get_payload():
                ctype = payload.get_content_type()
                #print ctype
                if ctype in ['text/plain']:
                    #print 'Body >>>>>>>>>' + payload.get_payload()
                    self.email_fields = self.parse_email_body(str(payload.get_payload()))
                    print 'Finished parsing email body'

                elif ctype in ['application/octet-stream']:
                    # This the attachment
                    attachment_name = "/tmp/" + self.alertName +payload.get_filename()
                    open(attachment_name, 'wb').write(payload.get_payload(decode=True))
                    print 'Finished writing attachment file at: %s' % attachment_name
                else :
                    print 'Unknown ctype: %s' % ctype
        else:
            print "Not a multi part email not sure how to process this"
        self.unzip_attachment(attachment_name)
        self.post_alerts()

    def parse_email_body(self, email_body):
        email_body_data = {}
        if len(email_body) == 0:
            print 'Email body is empty, nothing to parse'
            return
        for token in email_body.split("\n"):
            field = ""
            field_value = ""
            if '=' in token:
                field = token.split("=")[0].strip('\n')
                field = field.lower()
                field_value = token.split("=")[1].strip('\n')
            else:
                print 'Unparsable property encountered in email body %s, skipping' % token
                continue
            email_body_data[field] = field_value
        return email_body_data

    def parse_alert_data(self):
        self.tempDir

alerts = Alerts()
#alerts.unzip_attachment("/Users/cmutgi/ASUP/attachments/body.7z")
alerts.parse_email(sys.argv[1])
#alerts.get_alerts()
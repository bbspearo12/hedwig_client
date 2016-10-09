import requests
import ConfigParser
import email
import time
from requests.auth import HTTPBasicAuth
import sys
from email.header import decode_header

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

    def get_mail_header(self, header_text, default="ascii"):
        """Decode header_text if needed"""
        try:
            headers = decode_header(header_text)
        except email.Errors.HeaderParseError:
            # This already append in email.base64mime.decode()
            # instead return a sanitized ascii string
            return header_text.encode('ascii', 'replace').decode('ascii')
        else:
            for i, (text, charset) in enumerate(headers):
                try:
                    headers[i] = unicode(text, charset or default, errors='replace')
                except LookupError:
                    # if the charset is unknown, force default
                    headers[i] = unicode(text, default, errors='replace')
            return u"".join(headers)

    # This function assumes subject is of the format
    # HA Group Notification from netapp06 (MANAGEMENT_LOG) INFO
    # where the type is in the braces
    def get_asup_type(self, subj):

        severity = utils.get_asup_severity(subj)
        print "Severity: %s" % severity
        return at + " " + severity



    def parse_email(self, emailFile):
        # TODO validate email_file really exists
        print 'About to parse %s' % emailFile
        attachment_name = ""
        emailf = open(emailFile, 'rb')
        parsedEmail = email.message_from_file(emailf)
        email_fields = {}
        subj = self.get_mail_header(parsedEmail.get("subject", ""))
        print "Subject: %s" % subj

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
        email_fields['asup_type'] = utils.get_asup_type(subj, '(', ')')
        email_fields['asup_severity'] = utils.get_asup_severity(subj)
        utils.cleanup(self.tempDir)
        return email_fields, all_files


alerts = ASUP_Client()
utils = Utils()
required_files_data, all_files_data = alerts.parse_email(sys.argv[1])
alerts.post_required_files(required_files_data)
alerts.post_all_files(all_files_data)


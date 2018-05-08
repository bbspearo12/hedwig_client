import os
import ConfigParser
import subprocess
import shutil
import re


class Utils():
    max_depth = 100
    def __init__(self):
        config = ConfigParser.RawConfigParser()
        configFilePath = r'hedwig.cfg'
        config.read(configFilePath)
        self.appConf = config
        self.email_constants = {}
        self.files_data = {}
        self.required_files_data = {}
        self.depth = 0
        for opt in config.options('constants'):
            self.email_constants[config.get('constants', opt)] = True

    # Finds ASUP type elcosed between 2 braces in the subj line, example
    # HA Group Notification from netapp01 (HA GROUP ERROR: DISK/SHELF COUNT MISMATCH) ERROR
    @staticmethod
    def get_asup_type(s, first, last):
        try:
            start = s.find(first) + len(first)
            end = s.rfind(last)
            return s[start:end]
        except ValueError:
            return ""

    # Function returns severity of the asup
    # Based on the assumption that asup is of the format
    # HA Group Notification from netapp01 (CHASSIS UNDER TEMPERATURE) WARNING
    @staticmethod
    def get_asup_severity(s):
        return s.rsplit(None, 1)[-1]

    def parse_attachments(self, unzipped_files_dir, required_files):
        self.parse_alert_data(unzipped_files_dir, required_files)
        return self.required_files_data, self.files_data

    def parse_alert_data(self, unzipped_files_dir, required_files):
        files_to_parse = []
        file_count = 0
        print "Analyzing dir %s" % unzipped_files_dir
        if self.depth >= Utils.max_depth:
            print "Reached max depth terminating: %s" % self.depth
            return
        for file in os.listdir(unzipped_files_dir):
            print "Analyzing file %s" % unzipped_files_dir+"/"+file
            #print 'Adding file %s' % file
            if os.path.isdir(unzipped_files_dir+"/"+file) == True:
                print '%s is a dir, recursing' % str(unzipped_files_dir +"/"+ file)
                self.depth = self.depth + 1
                self.parse_alert_data(unzipped_files_dir +"/"+ file, required_files)
            elif os.path.isfile(unzipped_files_dir+"/"+file):
                file_count = file_count + 1
                if str(file).lower().endswith("txt") or '.' not in str(file):
                    files_to_parse.append(file)
                    fp = open(unzipped_files_dir + "/" + file, 'r')
                    file_content = str(fp.read())
                    file_content = file_content.replace("\r\n", "<br/>", -1)
                    file_content = file_content.replace("\n", "<br/>", -1)
                    file_content = file_content.replace("\t", "<tab/>", -1)
                    self.files_data[file] = "<br/>" + file_content + "<br/>"
                    fp.close()
                    if str(file) in required_files:
                        #print 'Adding to required files: %s' % str(file)
                        self.required_files_data[file] =  "<br/>" + file_content + "<br/>"
                elif str(file).lower().endswith(".gz"):
                    print "looks like a bundle, will unzip %s" % file
                    flist = [file]
                    self.unzip_file(flist, unzipped_files_dir+'/')
                    self.depth = self.depth + 1
                    self.parse_alert_data(unzipped_files_dir + "/" + file.replace(".", "_"), required_files)
                else:
                    print "skipped file %s" % file
        #print 'Files to parsed: ' + str(files_to_parse)
        #print "File data is %s" % self.files_data
        return

    def unzip_file(self, attachments, temp_dir):
        # TODO validate attachmentPath exists
        sevenz = self.appConf.get('hedwig', '7z')
        tar = self.appConf.get('hedwig', 'tar')
        for attachment in attachments:
            print("Will unzip: " + attachment)
            decom_dir = temp_dir+attachment.replace(".", "_") +"/"
            os.mkdir(decom_dir)
            if ".tar" in attachment:
                decompress = subprocess.check_output([tar, 'xf', temp_dir + "/" + attachment, '-C', decom_dir])
                print("Decompressed: " + attachment + " to location: " + decom_dir)
            else:
                decompress = subprocess.check_output([sevenz, 'x', '-o' + decom_dir, temp_dir + "/" + attachment])
                print("Decompressed: " + attachment + " to location: " + decom_dir )

    def parse_email_body(self, email_body):
        email_body_data = {}
        file_data_parsed_from_body = {}
        if len(email_body) == 0:
            print 'Email body is empty, nothing to parse'
            return
        start_file = False
        content = ""
        file_name = ""
        for line in email_body.split("\n"):
            isdelimiter, tmp_file_name = Utils.parseDelimiter(line)
            if isdelimiter:
                if start_file:
                    file_data_parsed_from_body[file_name] = content
                    print "We finished of reading file %s and content is %s" % (file_name, content)
                    file_name = tmp_file_name+".txt"
                    content = ""
                else:
                     file_name=tmp_file_name+".txt"
                     start_file = True
                     content = ""
                     print "Marking start of reading content for %s" % file_name
            elif start_file:
                content += line
                continue
            elif start_file == False and '=' in line:
                field = line.split("=")[0].strip('\n')
                if self.email_constants.has_key(field):
                    field = field.lower()
                    field_value = line.split("=")[1].strip('\n')
                    email_body_data[field] = field_value

        print "Parsed email body %s and file contents are %s " % (email_body_data, file_data_parsed_from_body)
        return email_body_data, file_data_parsed_from_body

    def cleanup(self, temp_dir):
        shutil.rmtree(temp_dir)
        print 'Cleaned up: ' + temp_dir

    @staticmethod
    def parseDelimiter(line):
        fileName_regex = '===== (.*) ====='
        if len(line) > 0 and re.search(fileName_regex, line) and len(re.search(fileName_regex, line).group(1)) > 0:
            #print "%s" % re.search(fileName_regex, line).group(1)
            return True, re.search(fileName_regex, line).group(1)
        else:
            #print "%s did not match regex "  % line
            return False, ""

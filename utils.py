import os
import ConfigParser
import subprocess
import shutil


class Utils():
    def __init__(self):
        config = ConfigParser.RawConfigParser()
        configFilePath = r'hedwig.cfg'
        config.read(configFilePath)
        self.appConf = config

    @staticmethod
    def parse_alert_data(unzipped_files_dir, required_files):
        files_to_parse = []
        files_data = {}
        required_files_data = {}
        file_count = 0
        # change unzipped_files_dir to self.tempDir TODO
        for file in os.listdir(unzipped_files_dir):
            #print 'Adding file %s' % file
            if os.path.isfile(unzipped_files_dir+"/"+file):
                file_count = file_count + 1
                if 'txt' not in str(file):
                    print 'Skipping file %s' % str(file)
                    continue
                # if file_count < 80:
                #     print 'Skipping file %s with count %d' % (str(file), file_count)
                #     continue
                # if file_count == 95:
                #     print 'Processed: %d files, stopping' % file_count
                #     break
                # if file_count < 95:
                #     print 'Skipping: %d files, continuing' % file_count
                #     continue
                files_to_parse.append(file)
                #if 'SYSCONFIG-A.txt' in str(file):
                fp = open(unzipped_files_dir + "/" + file, 'r')
                file_content = str(fp.read())
                file_content = file_content.replace("\r\n", "<br/>", -1)
                file_content = file_content.replace("\n", "<br/>", -1)
                #file_content = file_content.replace("\t", "", -1)
                file_content = file_content.replace("\t", "<tab/>", -1)
                #file_content = file_content.replace("\t", "&emsp;&emsp;&emsp;&emsp;", -1)
                files_data[file] = "<br/>" + file_content + "<br/>"
                #files_data[file] = str(fp.read())
                #print files_data[file]
                fp.close()
                #files_data[file] = files_data[file]
                if str(file)  in required_files:
                    print 'Adding to required files: %s' % str(file)
                    required_files_data[file] =  "<br/>" + file_content + "<br/>"
               # files_data[file] = files_data[file] + "-------------------------------------------------------------------------<br/>"
        print 'Files to parsed: ' + str(files_to_parse)
        return required_files_data, files_data

    def unzip_attachment(self, attachmentPath, temp_dir):
        # TODO validate attachmentPath exists
        print("Will unzip: " + attachmentPath)
        sevenz = self.appConf.get('hedwig', '7z')
        decompress = subprocess.check_output([sevenz, 'x', "-o" + temp_dir, attachmentPath])
        print("Decompressed: " + attachmentPath + " to location: " + temp_dir + ", output is: " + decompress)

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

    def cleanup(self, temp_dir):
        shutil.rmtree(temp_dir)
        print 'Cleaned up: ' + temp_dir
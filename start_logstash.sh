#!/bin/bash
/opt/logstash/bin/logstash  -f replaceme_with_logstashconf >> /var/log/asup_client.logs &
echo "logstash started; logs redirected to /var/log/asup_client.logs"
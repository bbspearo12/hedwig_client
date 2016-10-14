#!/bin/bash

OS="unknown"
banner(){
    echo "************************Welcome to hedwig setup***************************"
    echo "This script will help setup the following components:"
    echo "1. OpenJDK 1.7"
    echo "2. Logstash"
    echo "3. Python"
    ﻿﻿echo "4. Python-pip"
    echo "5. Git"
    echo "6. 7z Archive tool"
    echo "7. Hedwig Client"
    echo "Note: The script assumes, postfix server is setup and properly configured"
    echo "**************************************************************************"

}
pre-verifications(){
    echo "Performing pre-setup verification"
    if [ -f /etc/oracle-release ]; then
        OS=$(cat /etc/oracle-release | sed s/\ release.*//)
    fi

    if [ -n "$OS" ] || [ "$OS" != "﻿Oracle Linux Server" ]; then
        echo "OS: $OS is not OEL"
        exit -1;
    fi
    echo "Verified OS: $OS"
}

banner
pre-verifications
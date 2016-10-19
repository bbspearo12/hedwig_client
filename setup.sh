#!/bin/bash

OS="unknown"
INSTALL_JDK=0
MAILDIR_PATH=""
HEDWIG_CLIENT_GIT_REPO="https://github.com/chmutgi/hedwig_client.git"
HEDWIG_ENDPOINT=""
HEDWIG_SETUP_URL="https://raw.githubusercontent.com/chmutgi/hedwig_client/master/setup.sh"
LOGSTASH_CONF_LOCATION=""
ASUP_CLIENT_LOGS="/var/log/asup_client.logs"
HEDWIG_CLIENT_PATH=""
PYTHON_27_LOCATION=""
banner(){
    echo ""
    echo "************************Welcome to hedwig setup***************************"
    echo "This script will help setup the following components:"
    echo "1. OpenJDK 1.8"
    echo "2. Logstash"
    echo "3. Python"
    echo "4. Python-pip"
    echo "5. Git"
    echo "6. 7z Archive tool"
    echo "7. Hedwig Client"
    echo "Note: The script assumes, postfix server is setup and properly configured"
    echo "**************************************************************************"
    echo ""
}

pre-verifications(){
    echo "Performing pre-setup verification"
    if [ -f /etc/oracle-release ]; then
        OS=$(awk '{print $1}' /etc/oracle-release)
    fi
    if [ $OS == "Oracle" ]; then
            echo "Verified OS: $OS"
    else
        echo "OS: $OS is not Oracle Linux Server"
        exit -1;
    fi
    # add epel for python
    rpm -Uvh http://mirrors.kernel.org/fedora-epel/6/i386/epel-release-6-8.noarch.rpm

}

print-usage() {
    echo "Usage: curl ${HEDWIG_SETUP_URL} | bash -s -- <maildir> <hedwig-server-ip> <hedwig-admin-password>"
    exit -1;
}

read-args() {
    if [ "$#" -ne "3" ]; then
        print-usage
    fi
    if [ ! -d "$1" ]; then
        echo "Dir $1 does not exist, this is directory where new mail arrives, please check and restart setup"
        exit -1;
    fi
    MAILDIR_PATH=$1;
    HEDWIG_ENDPOINT=$2;
    HEDWIG_ADMIN_PASSWORD=$3;
    echo "Configured to read new mail from $MAILDIR_PATH"
    echo "Configured hedwig server ip to : $HEDWIG_ENDPOINT"

}

vercomp () {
    if [[ $1 == $2 ]]
    then
        return 0
    fi
    local IFS=.
    local i ver1=($1) ver2=($2)
    # fill empty fields in ver1 with zeros
    for ((i=${#ver1[@]}; i<${#ver2[@]}; i++))
    do
        ver1[i]=0
    done
    for ((i=0; i<${#ver1[@]}; i++))
    do
        if [[ -z ${ver2[i]yu} ]]
        then
            # fill empty fields in ver2 with zeros
            ver2[i]=0
        fi
        if ((10#${ver1[i]} > 10#${ver2[i]}))
        then
            return 1
        fi
        if ((10#${ver1[i]} < 10#${ver2[i]}))
        then
            return 2
        fi
    done
    return 0
}


# verify JDK
verify-jdk(){
if type -p java; then
    echo found java executable in PATH
    _java=java
elif [[ -n "$JAVA_HOME" ]] && [[ -x "$JAVA_HOME/bin/java" ]];  then
    echo found java executable in JAVA_HOME
    _java="$JAVA_HOME/bin/java"
else
    echo "no java, will install"
    INSTALL_JDK=1
fi

local version=""
local vcomp=""

if [[ "$_java" ]]; then
    version=$("$_java" -version 2>&1 | awk -F '"' '/version/ {print $2}')
    if [[ "$version" == *1.7* ]]; then
        INSTALL_JDK=1
        echo "Java 1.7 found, will be removed"
        yum remove -y java-1.7.0-openjdk
        yum remove -y java-1.6.0-openjdk
    elif [[ "$version" == *1.6* ]]; then
        INSTALL_JDK=1
        echo "Java 1.6 found, will be removed"
        yum remove -y java-1.6.0-openjdk
    elif [[ "$version" == *1.8* ]]; then
        echo "Java 1.8 or above found, continuing..."
        INSTALL_JDK=0
    fi
fi
}

# install jdk if required
install-jdk(){

if [ "$INSTALL_JDK" -eq "1" ]; then
    echo "Installing JDK 1.8"
    wget --no-check-certificate --no-cookies --header 'Cookie: oraclelicense=accept-securebackup-cookie' http://download.oracle.com/otn-pub/java/jdk/8u5-b13/jdk-8u5-linux-x64.rpm -O jdk-8u5-linux-x64.rpm
    rpm -ivh jdk-8u5-linux-x64.rpm
    alternatives --install /usr/bin/java java /usr/java/jdk1.8.0_05/jre/bin/java 20000
    alternatives --install /usr/bin/jar jar /usr/java/jdk1.8.0_05/bin/jar 20000
    alternatives --install /usr/bin/javac javac /usr/java/jdk1.8.0_05/bin/javac 20000
    alternatives --install /usr/bin/javaws javaws /usr/java/jdk1.8.0_05/jre/bin/javaws 20000
elif [ "$INSTALL_JDK" -eq "2" ]; then
    echo "Upgrading JDK"
    yum install -y java-1.8.0-openjdk-devel
    verify-jdk
    if [ "$INSTALL_JDK" -ne "0" ]; then
        echo "Failed to upgrade java"
        exit -1
    fi
else
    echo "Verified JDK, continuing...."
fi
}

# install logstash
install-logstash() {
if type -p logstash; then
    echo found logstash executable in PATH
    _logstash=logstash
# verify  if it got installed in /opt/logstash
elif [[ -f "/opt/logstash/bin/logstash" ]]; then
    echo "Logstash found at /opt/logstash/"
    _logstash="/opt/logstash/bin/logstash"
else
    rpm --import https://packages.elastic.co/GPG-KEY-elasticsearch
cat <<EOF >/etc/yum.repos.d/logstash.repo
[logstash-2.4]
name=Logstash repository for 2.4.x packages
baseurl=https://packages.elastic.co/logstash/2.4/centos
gpgcheck=1
gpgkey=https://packages.elastic.co/GPG-KEY-elasticsearch
enabled=1
EOF
    yum install -y logstash
    echo "Installed logstash"
fi

local version=""
local vcomp=""
if [[ "$_logstash" ]]; then
    echo "Verifying logstash version"
    version=$("$_logstash" --version | awk '{print $2}')
    vcomp=$(vercomp $version 2.4.0)
    if [[ $vcomp -le 1 ]]; then
        echo "Logstash version is $version more than 2.3.0"
    else
        echo "Logstash version is less than 2.3.0, Please upgrade."
        exit -1
    fi
fi
touch $ASUP_CLIENT_LOGS
echo "Verified Logstash"
}


install-py-27() {
    echo "Python version is not 2.7, installing in /usr/local/lib"
    yum groupinstall -y 'development tools' &> /tmp/development_tools_details.txt
    if [ "$?" -ne "0" ]; then
        echo "Failed to install python. Please fix errors in '/tmp/development_tools_details.txt' and restart"
        exit -1
    fi
    yum install -y zlib-devel bzip2-devel openssl-devel xz-libs wget &> /tmp/misctools_install_details.txt
    if [ "$?" -ne "0" ]; then
        echo "Failed to install misc tools requried for python. Please fix errors in '/tmp/misctools_install_details.txt' and restart"
        exit -1
    fi
    echo "Successfully installed misc tools for python"
    pushd $PWD
    cd /usr/local/lib
    echo "Downloading source for python 2.7.8"
    wget http://www.python.org/ftp/python/2.7.8/Python-2.7.8.tar.xz -O Python-2.7.8.tar.xz
    xz -d Python-2.7.8.tar.xz
    tar -xvf Python-2.7.8.tar
    pushd $PWD
    cd Python-2.7.8
    ./configure --prefix=/usr/local &> /tmp/py_configure_details.txt
    if [ "$?" -ne "0" ]; then
        echo "Failed to configure python. Please fix errors in '/tmp/py_configure_details.txt' and restart"
        exit -1
    fi
    echo "Successfully configured python 2.7.8"
    make && make altinstall &> /tmp/py_make_install_details.txt
    if [ "$?" -ne "0" ]; then
        echo "Failed to configure python. Please fix errors in '/tmp/py_make_install_details.txt' and restart"
        exit -1
    fi
    echo "Successfully completed make install of python 2.7.8"
    popd
    popd
    echo "Python installation complete changed working dir to $PWD"
}


install-python() {
if type -p python; then
    echo found python executable in PATH
    _python=python
fi
local version=""
local vcomp=""
if [[ "$_python" ]]; then
    echo "Verifying python version"
    version=$("$_python" --version 2>&1 | awk '{print $2}')
    if [[ "$version" == *2.6* ]]; then
        install-py-27
    elif [[ "$version" == *2.7* ]]; then
        echo Python version is equal to or more than 2.7.0, continuing.
    fi
else
    echo "Python not installed, or not in PATH. Installing python 2.7"
    install-py-27
fi
    PYTHON_27_LOCATION=$(which python2.7)
    echo "Python installation verified"
}

install-pip() {
if type -p pip; then
    echo "found pip executable in PATH"
    _pip=pip
else
    echo "Installing python pip"
    wget --no-check-certificate https://bootstrap.pypa.io/get-pip.py
    python2.7 get-pip.py
    if [ "$?" -ne "0" ]; then
        echo "Failed to install pip. Please manually install pip from 'https://pip.pypa.io/en/stable/installing/' and restar"
        exit -1
    fi
    _pip=pip
fi
echo "Installed and verified pip and requests module"
}

install-py-modules() {
    echo "Verifying python requests module version"
    version=$("$_pip" freeze | grep requests | awk -F "==" '{print $2}')
    vcomp=$(vercomp $version 2.11.0)
    if [[ -n $version ]] && [[ "$vcomp" -le 1 ]]; then
        echo Requests version is $version more than 2.11.0
    else
        echo Requests is not installed or not upto date; upgrading.
        pip install requests==2.11.1
    fi
}


install-7z() {
if type -p 7z; then
    echo "found 7z executable in PATH"
else
    yum install -y  p7zip p7zip-plugins &> /tmp/7z_install_details.txt
    if grep -qi error /tmp/7z_install_details.txt; then
        echo "Failed to install 7z, please fix error and restart setup"
        exit -1
    fi
fi
_7z=`type -p 7z`
}

install-git() {
if type -p git; then
    echo "found git executable in PATH"
    _git=git
else
    echo "Installing git"
    yum install -y git &> /tmp/git_install_details.txt
    if [ "$?" -ne "0" ]; then
        echo "Failed to install git. Please fix errors in '/tmp/git_install_details.txt' and restart"
        exit -1
    fi
fi
}

clone-hedwig-client() {
    git clone ${HEDWIG_CLIENT_GIT_REPO}
    HEDWIG_CLIENT_PATH="$(pwd)/hedwig_client"
    echo "Updating hedwig client path to ${HEDWIG_CLIENT_PATH}"
    echo "Updating Hedwig server endpoint to ${HEDWIG_ENDPOINT}"
    sed -i s/localhost/${HEDWIG_ENDPOINT}/g hedwig_client/hedwig.cfg
    echo "Updating admin credentials"
    sed -i s/replaceme/${HEDWIG_ADMIN_PASSWORD}/g hedwig_client/hedwig.cfg
    echo "Updating 7z location"
    z_path=`cat hedwig_client/hedwig.cfg|grep 7z|awk -F "=" '{print $2}'`
    sed -i 's|'${z_path}'|'$_7z'|g' hedwig_client/hedwig.cfg
}

update-logstash-conf() {
    echo "Updating logstash configuration"
    sed -i 's|maildir|'$MAILDIR_PATH'|g' hedwig_client/hedwig-logstash.conf
    sed -i 's|newpath|'$HEDWIG_CLIENT_PATH'|g' hedwig_client/hedwig-logstash.conf
    sed -i 's|python|'$PYTHON_27_LOCATION'|g' hedwig_client/hedwig-logstash.conf
    #logstash-conf-path="${HEDWIG_CLIENT_PATH}/hedwig-logstash.conf"
    sed -i 's|replaceme_with_logstashconf|'$HEDWIG_CLIENT_PATH/hedwig-logstash.conf'|g' hedwig_client/start_logstash.sh
}

run-logstash() {
    /bin/bash hedwig_client/start_logstash.sh
}

banner
read-args $@
pre-verifications
install-python
verify-jdk
install-jdk
install-logstash
install-pip
install-py-modules
install-7z
install-git
clone-hedwig-client
update-logstash-conf
run-logstash

echo ******Successfully completed hedwig client setup********
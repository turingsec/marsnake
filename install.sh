#!/bin/sh

#################################################################################
#
#	Marsnake
#
#
#
#################################################################################
echo -e \
"   __  __                            _           \n"\
"  |  \/  |                          | |          \n"\
"  | \  / | __ _ _ __ ___ _ __   __ _| | _____    \n"\
"  | |\/| |/ _  |  __/ __|  _  \/ _  | |/ / _ \   \n"\
"  | |  | | (_| | |  \__ \ | | | (_| |   <  __/   \n"\
"  |_|  |_|\__,_|_|  |___/_| |_|\__,_|_|\_\___|   \n"

#echo "What is Marsnake: "

COMPANY="Turing Security Technology Co., Ltd."
COMPANY_ABBR="turingsec"
PROGRAM="marsnake"
PROGRAM_VERSION="v0.2"
PROGRAM_RELEASE_DATE="Oct 2017"
PROGRAM_URL="https://www.marsnake.com"

WORKDIR=$(pwd)
HOME_DIR=${HOME}
DISPLAY_LANG="${LANG}"
INCLUDE_DIR="include"

#Service Manager
SYSTEMD_SERVICE="${PROGRAM}.service"
SYSV_SERVICE="${PROGRAM}"

#Installation Directory
INSTALLATION_DIR="/usr/share"

#Config
HARDWARE_INFO_FILE="config/hardware.info"
INSTALL_LOG="installation.log"

RSA_PRIVATE_KEY="config/private_key_2048.pem"
RSA_PUBLIC_KEY="config/public_key_2048.pem"
CREDENTIAL_FILE="config/credential"

. ${INCLUDE_DIR}/constants
. ${INCLUDE_DIR}/functions

# Make sure umask is sane
umask 022
trap Interrupt INT

if [ -z "${HOME_DIR}" ]; then HOME_DIR=$(echo ~ 2>/dev/null); fi

MYID=""

# Check user to determine file permissions later on. If we encounter Solaris, use related id binary instead
if [ -x /usr/xpg4/bin/id ]; then
    MYID=$(/usr/xpg4/bin/id -u 2> /dev/null)
elif [ $(uname) = "SunOS" ]; then
    MYID=$(id | tr '=' ' ' | tr '(' ' ' | awk '{ print $2 }' 2> /dev/null)
else
    MYID=$(id -u 2> /dev/null)
fi

if [ -z "${MYID}" ]; then
    Display --indent 2 --text "- Could not find user ID with id command"
    exit 1
fi

######################################
#
#   OS Detection
#
######################################
os_detect

######################################
#
#   Show system information
#
######################################
echo ""
echo "  ---------------------------------------------------"
echo "  Program version:           ${PROGRAM_VERSION}"
echo "  Program Release Date:      ${PROGRAM_RELEASE_DATE}"
echo "  Operating system:          ${OS}"
echo "  Operating system name:     ${OS_NAME}"
echo "  Operating system version:  ${OS_VERSION}"
echo "  Kernel version:            ${OS_KERNELVERSION}"
echo "  Hardware platform:         ${HARDWARE}"
echo "  Hostname:                  ${HOSTNAME}"
echo "  Home Directory:            ${HOME_DIR}"
echo "  ---------------------------------------------------"

######################################
#
#   Start as root
#
######################################
if [ ${MYID} -eq 0 ]; then
    PRIVILEGED=1
    SUDO=""
    Display --indent 2 --text "- Starting ${PROGRAM} as root" --result "YES" --color GREEN
else
    PRIVILEGED=0
    SUDO="sudo "
    Display --indent 2 --text "- Starting ${PROGRAM} as root" --result "NO" --color WARNING
fi

######################################
#
#   Check Essential Binary
#
######################################
InsertSection "Checking Essential Binary"
SearchRequiredBinary

if [ ! -z "${PYTHON_BINARY}" ]; then
    PYTHON_VERSION=$(${PYTHON_BINARY} -c "import platform;print(platform.python_version())")
    Display --indent 2 --text "- python" --result ${PYTHON_VERSION} --color GREEN
else
    Display --indent 2 --text "- python" --result "NOT FOUND" --color RED
    exit 1
fi

if [ ! -z "${PIP_BINARY}" ]; then
    PIP_VERSION=$(${PYTHON_BINARY} -c "import pip;print(pip.__version__)")
    Display --indent 2 --text "- pip" --result ${PIP_VERSION} --color GREEN
else
    Display --indent 2 --text "- pip" --result "NOT FOUND" --color RED

    if [ ${PRIVILEGED} -eq 1 ]; then
        CHECK="Y"
    else
        read -p "Do you want to install pip?(Y/n): " CHECK
    fi

    if [ "$CHECK" = "" -o "$CHECK" = "Y" -o "$CHECK" = "y" ]; then
        ${SUDO}${PYTHON_BINARY} ${INCLUDE_DIR}/get-pip.py

        if [ $? -eq 0 ]; then
            Display --indent 2 --text "- Install pip" --result DONE --color GREEN
        else
            Display --indent 2 --text "- Install pip" --result FAILED --color WARNING
            exit 1
        fi

    else
        Display --indent 2 --text "- You need to install pip to continue"
        exit 1
    fi
fi

######################################
#
#   Check Essential Package
#
######################################
InsertSection "Checking Essential Package"

if [ ! -z "${RPM_BINARY}" ]; then
    CHANGELOG_DEV="yum-changelog yum-plugin-changelog"
    InstallPackage "${CHANGELOG_DEV}" "yum-changelog"
fi

if [ ! -z "${DNF_BINARY}" ]; then
    REDHAT_RPM_CONFIG="redhat-rpm-config"
    InstallPackage "${REDHAT_RPM_CONFIG}" "Red Hat specific rpm configuration files"
fi

PYTHON2_DEV="python-dev python-devel python2-devel"
InstallPackage "${PYTHON2_DEV}" "Python Development Tools"

#MYSQL_DEV="libmysqlclient-dev mysql-devel mariadb-devel"
#InstallPackage "${MYSQL_DEV}" "Mysql Development Tools"

LSHW_PACKAGE="lshw"
InstallPackage "${LSHW_PACKAGE}" "lshw"

OPENSSL_PACKAGE="openssl"
InstallPackage "${OPENSSL_PACKAGE}" "OpenSSL toolkit"

GCC_PACKAGE="gcc"
InstallPackage "${GCC_PACKAGE}" "GNU Compiler Collection"

#search again
SearchRequiredBinary

######################################
#
#   Check Essential Python Modules
#
######################################
InsertSection "Checking Essential Python Modules"
REQUIRED_MODULES="psutil pycrypto futures"

#python-magic beautifulsoup4 paramiko redis pymongo MySQL-python lxml

CheckPythonModuleInstalled ${REQUIRED_MODULES}

################################################
#
#   Python Essential Module Will to be installed
#
################################################
if [ ! -z "${NOT_INSTALL_MODULES}" ]; then
    InsertSection "Following Python Module Will Be Installed"

    for I in ${NOT_INSTALL_MODULES}; do
        Display --indent 2 --text "- ${I}"
    done

    InsertEmptyLine
    InstallPythonModule ${NOT_INSTALL_MODULES}
fi

##################################################
#
#   Generate an RSA keypair
#
##################################################
InsertSection "Generate an RSA keypair"

RESULT=$(${OPENSSL_BINARY} genpkey -algorithm RSA -out ${RSA_PRIVATE_KEY} -pkeyopt rsa_keygen_bits:2048 2> /dev/null)

if [ $? -eq 0 ]; then
    Display --indent 2 --text "- Generate an RSA keypair with a 2048 bit private key" --result DONE --color GREEN
else
    Display --indent 2 --text "- Generate an RSA keypair with a 2048 bit private key" --result FAILED --color GREEN
    exit 1
fi

RESULT=$(${OPENSSL_BINARY} rsa -pubout -in ${RSA_PRIVATE_KEY} -out ${RSA_PUBLIC_KEY} 2> /dev/null)

if [ $? -eq 0 ]; then
    Display --indent 2 --text "- Extracting the public key from an RSA keypair" --result DONE --color GREEN
else
    Display --indent 2 --text "- Extracting the public key from an RSA keypair" --result FAILED --color GREEN
    exit 1
fi

##################################################
#
#   Use lshw to generate hardware information file
#
##################################################
InsertSection "Generate hardware information file"

if [ ${PRIVILEGED} -eq 0 ]; then
    Display --indent 2 --text "- Require root permission to use lshw to fully list hardware"
else
    Display --indent 2 --text "- Use lshw to fully list hardware"
fi

RESULT=$(${SUDO}${LSHW_BINARY} -json > ${HARDWARE_INFO_FILE} 2>/dev/null)

if [ $? -eq 0 ]; then
    Display --indent 2 --text "- Writing hardware information into ${HARDWARE_INFO_FILE}" --result DONE --color GREEN
else
    Display --indent 2 --text "- Writing hardware information into ${HARDWARE_INFO_FILE}" --result FAILED --color WARNING
fi

######################################
#
#   Associate Your Device and Cloud Account
#
######################################
InsertSection "Associate Your Device and Cloud Account"

. ${INCLUDE_DIR}/associate_cloud_account.sh

if [ ${RESULT} -eq 0 ]; then
    Display --indent 2 --text "- Create user credential" --result DONE --color GREEN
elif [ ${RESULT} -eq 1 ]; then
    Display --indent 2 --text "- User credential exists" --result DONE --color GREEN
else
    Display --indent 2 --text "- Cannot create user credential"
    exit 1
fi

######################################
#
#   start at next reboot
#
######################################
InsertSection "Start ${PROGRAM} automatically on boot"

read -p "We suggest you to enable ${PROGRAM} at startup (Y/n): " CHECK

if [ "${CHECK}" = "" -o "${CHECK}" = "Y" -o "${CHECK}" = "y" ]; then
    AUTO_STARTING=0
    TMP_WORKDIR=$(echo ${WORKDIR} | sed 's/\//\\\//g')
    TMP_PYTHON_BINARY=$(echo ${PYTHON_BINARY} | sed 's/\//\\\//g')

    cp ${INCLUDE_DIR}/${SYSV_SERVICE}.template ${INCLUDE_DIR}/${SYSV_SERVICE}
    
    sed -i 's/#dir=/dir="'${TMP_WORKDIR}'"/g' ${INCLUDE_DIR}/${SYSV_SERVICE}
    sed -i 's/#cmd=/cmd="'${TMP_PYTHON_BINARY}' start.py"/g' ${INCLUDE_DIR}/${SYSV_SERVICE}

    chmod +x ${INCLUDE_DIR}/${SYSV_SERVICE}

    if [ ! -z "${SYSTEMCTL_BINARY}" ]; then
        #As SELINUX policy limit, We had to copy init script into /usr/share directory
        ${SUDO}mkdir -p "${INSTALLATION_DIR}/${COMPANY_ABBR}/"
        INIT_SCRIPT="${INSTALLATION_DIR}/${COMPANY_ABBR}/${SYSV_SERVICE}"

        cp ${INCLUDE_DIR}/${SYSTEMD_SERVICE}.template ${INCLUDE_DIR}/${SYSTEMD_SERVICE}
        
        sed -i 's/#WorkingDirectory=/WorkingDirectory='${TMP_WORKDIR}'/g' ${INCLUDE_DIR}/${SYSTEMD_SERVICE}
        sed -i 's/#ExecStart=/ExecStart='$(echo ${INIT_SCRIPT} | sed 's/\//\\\//g')' start/g' ${INCLUDE_DIR}/${SYSTEMD_SERVICE}
        #sed -i 's/#ExecStart=/ExecStart='${TMP_PYTHON_BINARY}' start.py/g' ${INCLUDE_DIR}/${SYSTEMD_SERVICE}

        ${SUDO}cp ${INCLUDE_DIR}/${SYSTEMD_SERVICE} /etc/systemd/system/
        ${SUDO}cp ${INCLUDE_DIR}/${SYSV_SERVICE} ${INIT_SCRIPT}
        
        if [ $? -eq 0 ]; then
            RESULT=$(${SUDO}${SYSTEMCTL_BINARY} enable ${SYSTEMD_SERVICE} 2> /dev/null)
            RESULT=$(${SUDO}${SYSTEMCTL_BINARY} daemon-reload)

            if [ $? -eq 0 ]; then
                AUTO_STARTING=1
            fi
        fi

    elif [ ! -z "${UPDATERCD_BINARY}" ]; then
        ${SUDO}cp -f ${INCLUDE_DIR}/${SYSV_SERVICE} /etc/init.d/

        if [ $? -eq 0 ]; then
            RESULT=$(${SUDO}${UPDATERCD_BINARY} ${SYSV_SERVICE} enable 2> /dev/null)
            
            if [ $? -eq 0 ]; then
                AUTO_STARTING=1
            fi
        fi

    elif [ ! -z "${CHKCONFIG_BINARY}" ]; then
        ${SUDO}cp -f ${INCLUDE_DIR}/${SYSV_SERVICE} /etc/init.d/

        if [ $? -eq 0 ]; then
            RESULT=$(${SUDO}${CHKCONFIG_BINARY} --add ${SYSV_SERVICE})
            RESULT=$(${SUDO}${CHKCONFIG_BINARY} ${SYSV_SERVICE} on)
            
            if [ $? -eq 0 ]; then
                AUTO_STARTING=1
            fi
        fi

    elif [ ! -z "${INITCTL_BINARY}" ]; then
        echo "Not Implement Upstart service manager"
    else
        Display --indent 2 --text "- Unknown service manager" --result FAILED --color RED
        exit 1
    fi
    
    if [ ${AUTO_STARTING} -eq 1 ]; then
        Display --indent 2 --text "- Start ${PROGRAM} automatically on boot" --result DONE --color GREEN
    else
        Display --indent 2 --text "- Start ${PROGRAM} automatically on boot" --result FAILED --color WARNING
    fi
fi

######################################
#
#   Enjoy!
#
######################################
InsertSection "Enjoy ${PROGRAM}"

SUCCESS=0

if [ ! -z "${SYSTEMCTL_BINARY}" ]; then
    ${SUDO}${SYSTEMCTL_BINARY} restart ${SYSTEMD_SERVICE}
    
    if [ $? -eq 0 ]; then
        SUCCESS=1
    fi
elif [ ! -z "${UPDATERCD_BINARY}" -o ! -z "${CHKCONFIG_BINARY}" ]; then
    ${SUDO}/etc/init.d/${SYSV_SERVICE} start
    
    if [ $? -eq 0 ]; then
        SUCCESS=1
    fi
elif [ ! -z "${INITCTL_BINARY}" ]; then
    ${SUDO}${INITCTL_BINARY} start ${PROGRAM}

    if [ $? -eq 0 ]; then
        SUCCESS=1
    fi
fi

if [ ${SUCCESS} -eq 1 ]; then
    Display --indent 2 --text "- ${PROGRAM} running " --result DONE --color GREEN
    Display --indent 2 --text "- You can visit ${PROGRAM_URL} to manage your devices"
else
    Display --indent 2 --text "- ${PROGRAM} running " --result FAILED --color RED
fi
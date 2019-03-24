#!/bin/bash

# Paths where system and program binaries are located
BIN_PATHS="/bin /sbin /usr/bin /usr/sbin /usr/local/bin /usr/local/sbin \
          /usr/local/libexec /usr/libexec /usr/sfw/bin /usr/sfw/sbin \
          /usr/sfw/libexec /opt/sfw/bin /opt/sfw/sbin /opt/sfw/libexec \
          /usr/xpg4/bin /usr/css/bin /usr/ucb /usr/X11R6/bin /usr/X11R7/bin \
          /usr/pkg/bin /usr/pkg/sbin"
GREEN="\033[32m"
RED="\033[31m"
WHITE="\033[37m"
YELLOW="\033[33m"
WARNING="\033[35m"
NORMAL="\033[0m"

SearchRequiredBinary() {
    for SCANDIR in ${BIN_PATHS}; do
        if [ -d ${SCANDIR} ]; then
            #if [ -L ${SCANDIR} ]; then
            #    echo "${SCANDIR} is a symbol link"
            #fi

            FIND=$(ls ${SCANDIR})
            for FILENAME in ${FIND}; do
                BINARY="${SCANDIR}/${FILENAME}"
                
                case ${FILENAME} in
                    rpm)
                        RPM_BINARY=${BINARY}
                    ;;
                    dpkg)
                        DPKG_BINARY=${BINARY}
                    ;;
                    yum)
                        YUM_BINARY=${BINARY}
                    ;;
                    apt-get)
                        APTGET_BINARY=${BINARY}
                    ;;
                    dnf)
                        DNF_BINARY=${BINARY}
                    ;;
                    rm)
                        RM_BINARY=${BINARY}
                    ;;
                    git)
                        GIT_BINARY=${BINARY}
                    ;;
                    tar)
                        TAR_BINARY=${BINARY}
                    ;;
                    unxz)
                        UNXZ_BINARY=${BINARY}
                    ;;
                    gcc)
                        GCC_BINARY=${BINARY}
                    ;;
                    make)
                        MAKE_BINARY=${BINARY}
                    ;;
                    curl)
                        CURL_BINARY=${BINARY}
                    ;;
                    chmod)
                        CHMOD_BINARY=${BINARY}
                    ;;
                    systemctl)
                        SYSTEMCTL_BINARY=${BINARY}
                    ;;
                    initctl)
                        INITCTL_BINARY=${BINARY}
                    ;;
                    crontab)
                        CRONTAB_BINARY=${BINARY}
                    ;;
                esac
            done
        fi
    done
}

Display() {
    INDENT=0; TEXT=""; RESULT=""; COLOR=""; SPACES=0; SHOWDEBUG=0
    while [ $# -ge 1 ]; do
        case $1 in
            --color)
                shift
                    case $1 in
                      GREEN)   COLOR=$GREEN   ;;
                      RED)     COLOR=$RED     ;;
                      WHITE)   COLOR=$WHITE   ;;
                      YELLOW)  COLOR=$YELLOW  ;;
                    esac
            ;;
            --debug)
                SHOWDEBUG=1
            ;;
            --indent)
                shift
                INDENT=$1
            ;;
            --result)
                shift
                RESULT=$1
            ;;
            --text)
                shift
                TEXT=$1
            ;;
            *)
                echo "INVALID OPTION (Display): $1"
                ExitFatal
            ;;
        esac
        # Go to next parameter
        shift
    done

    if [ "${RESULT}" = "" ]; then
    	RESULTPART=""
    else
    	RESULTPART=" [ ${COLOR}${RESULT}${NORMAL} ]"
    fi

    if [ ! "${TEXT}" = "" ]; then
        # Display:
        # - counting with -m instead of -c, to support language locale
        # - wc needs LANG to deal with multi-bytes characters but LANG has been unset in include/consts...
        LINESIZE=$(export LC_ALL= ; export LANG="${DISPLAY_LANG}";echo "${TEXT}" | wc -m | tr -d ' ')
        if [ ${SHOWDEBUG} -eq 1 ]; then DEBUGTEXT=" [${PURPLE}DEBUG${NORMAL}]"; else DEBUGTEXT=""; fi
        if [ ${INDENT} -gt 0 ]; then SPACES=$((62 - INDENT - LINESIZE)); fi
        if [ ${SPACES} -lt 0 ]; then SPACES=0; fi

		# Check if we already have already discovered a proper echo command tool. It not, set it default to 'echo'.
		if [ "${ECHOCMD}" = "" ]; then ECHOCMD="env echo -e"; fi
		${ECHOCMD} "\033[${INDENT}C${TEXT}\033[${SPACES}C${RESULTPART}${DEBUGTEXT}"
	fi
}

CheckPackageInstalled() {
    PACKAGE_INSTALLED=0

    if [ ${LOW_LEVEL_PACKAGE_MANAGER} = 'rpm' ]; then
        ${RPM_BINARY} -q ${1} > /dev/null 2>&1
    elif [ ${LOW_LEVEL_PACKAGE_MANAGER} = 'dpkg' ]; then
        ${DPKG_BINARY} -s ${1} > /dev/null 2>&1
    fi

    if [ $? -eq 0 ]; then
        PACKAGE_INSTALLED=1
    fi
}

DoInstallPackage() {
    ${SUDO} ${HIGH_LEVEL_PACKAGE_MANAGER} -y install ${1}

    if [ $? -eq 0 ]; then
        PACKAGE_INSTALLED=1
    fi
}

InstallPackage() {
    #Check whether packages installed
	for I in ${1}; do
		CheckPackageInstalled ${I}
        
		if [ ${PACKAGE_INSTALLED} -eq 1 ]; then
			Display --indent 2 --text "- ${I}" --result "FOUND" --color GREEN
			continue
		else
			Display --indent 2 --text "- ${I}" --result "NOT FOUND" --color YELLOW
			Display --indent 2 --text "- Installing ${I}"
			DoInstallPackage ${I}

			if [ $PACKAGE_INSTALLED -eq 1 ]; then
				Display --indent 2 --text "- Install ${I}" --result "DONE" --color GREEN
			else
				Display --indent 2 --text "- Install ${I}" --result "ERROR" --color RED
				exit 1
			fi
		fi
    done
}

env echo -e '\033[0;36m'\
'   __  __                            _           \r\n'\
'  |  \/  |                          | |          \r\n'\
'  | \  / | __ _ _ __ ___ _ __   __ _| | _____    \r\n'\
'  | |\/| |/ _  |  __/ __|  _  \/ _  | |/ / _ \   \r\n'\
'  | |  | | (_| | |  \__ \ | | | (_| |   <  __/   \r\n'\
'  |_|  |_|\__,_|_|  |___/_| |_|\__,_|_|\_\___|   \r\n'\
'\033[0;0m'

DEST_DIR=${HOME}"/.Marsnake"
MARSNAKE_GIT_ADDR="https://github.com/turingsec/marsnake"
INSTALL_LOG=${DEST_DIR}"/install.log"

SearchRequiredBinary

if [ ${DPKG_BINARY} ] && [ ${APTGET_BINARY} ]; then
	LOW_LEVEL_PACKAGE_MANAGER='dpkg'
	Display --indent 1 --text "- Package manager" --result ${LOW_LEVEL_PACKAGE_MANAGER} --color GREEN
	HIGH_LEVEL_PACKAGE_MANAGER='apt-get'
	Display --indent 1 --text "- Package management tool" --result ${HIGH_LEVEL_PACKAGE_MANAGER} --color GREEN
elif [ ${RPM_BINARY} ]; then
	LOW_LEVEL_PACKAGE_MANAGER='rpm'
	Display --indent 1 --text "- Package manager" --result ${LOW_LEVEL_PACKAGE_MANAGER} --color GREEN
	if [ ${DNF_BINARY} ]; then
		HIGH_LEVEL_PACKAGE_MANAGER='dnf'
	elif [ ${YUM_BINARY} ]; then
		HIGH_LEVEL_PACKAGE_MANAGER='yum'
	else
		Display --indent 1 --text "- Package management tool" --result "NOT FOUND" --color RED
		exit 1
	fi
	Display --indent 1 --text "- Package management tool" --result ${HIGH_LEVEL_PACKAGE_MANAGER} --color GREEN
else
	Display --indent 1 --text "- Could not find packet manager"
	exit 1
fi

MYID=$(id -u 2> /dev/null)

if [ -z "${MYID}" ]; then
	Display --indent 1 --text "- Get process user ID" --result "FAILED" --color RED
	exit 1
elif [ ${MYID} -eq 0 ]; then
	Display --indent 1 --text "- Starting as root" --result "YES" --color GREEN
	SUDO=''
else
	Display --indent 1 --text "- Starting as root" --result "NO" --color YELLOW
	SUDO='sudo'
	Display --indent 2 --text '- Continue with sudo'
fi

Display --indent 1 --text "- Installing essential packages"

if [ ! ${GIT_BINARY} ] || [ ! ${TAR_BINARY} ] || [ ! ${UNXZ_BINARY} ] || [ ! ${GCC_BINARY} ] || [ ! ${MAKE_BINARY} ] || [ ! ${CURL_BINARY} ]; then
	if [ ! ${GIT_BINARY} ]; then
		InstallPackage "git"
	fi

	if [ ! ${TAR_BINARY} ]; then
		InstallPackage "tar"
	fi

	if [ ! ${UNXZ_BINARY} ]; then
		if [ ${LOW_LEVEL_PACKAGE_MANAGER} = "dpkg" ]; then
			InstallPackage "xz-utils"
		else
			InstallPackage "xz"
		fi
	fi

	if [ ! ${GCC_BINARY} ]; then
		InstallPackage "gcc"
	fi

	if [ ! ${MAKE_BINARY} ]; then
		InstallPackage "make"
	fi

	if [ ! ${CURL_BINARY} ]; then
		InstallPackage "curl"
	fi

	SearchRequiredBinary
fi

DPKG_PACKAGES="libc6 zlib1g zlib1g-dev libbz2-dev liblzma-dev libffi-dev libssl-dev libncurses5-dev libreadline6-dev libgdbm-dev libexpat1-dev libsqlite3-dev"
RPM_PACKAGES="glibc zlib krb5-libs libcom_err keyutils-libs libselinux zlib-devel bzip2-devel xz-devel libffi-devel openssl-devel ncurses-devel readline-devel gdbm-devel expat-devel sqlite-devel"

if [ ${LOW_LEVEL_PACKAGE_MANAGER} = "dpkg" ]; then
	InstallPackage "${DPKG_PACKAGES}"
else
	InstallPackage "${RPM_PACKAGES}"
fi

set -e
Display --indent 1 --text "- Marsnake is installing to "${DEST_DIR}

if [ ! -d ${DEST_DIR} ]; then
	${SUDO} mkdir --parents	${DEST_DIR}

	if [ ! -d ${DEST_DIR} ]; then
		Display --indent 2 --text "- Create Marsnake directory" --result "FAILED" --color RED
		exit 1
	fi
fi

Display --indent 2 --text "- Downloading Marsnake using git"

if [ ! -d ${DEST_DIR}"/marsnake" ];then
    ${SUDO} ${GIT_BINARY} clone ${MARSNAKE_GIT_ADDR} ${DEST_DIR}"/marsnake"
    
    if [ ! $? -eq 0 ]; then
	    Display --indent 2 --text "- Download Marsnake" --result "FAILED" --color RED
        exit 1
    fi
fi

Display --indent 2 --text "- Extracting python interpreter"
${SUDO} ${TAR_BINARY} -xJf ${DEST_DIR}"/marsnake/lib/Python-3.6.8.tar.xz" -C ${DEST_DIR}"/marsnake"

if [ ! $? -eq 0 ]; then
	Display --indent 2 --text "- Extract python interpreter" --result "FAILED" --color RED
    exit 1
fi

Display --indent 2 --text "- Compiling python interpreter"
Display --indent 3 --text "- Configure"

CONFIGURE_PREFIX=${DEST_DIR}"/marsnake/interpreter_install"
CONFIGURE_PARAMS="--enable-optimizations --enable-ipv6 --with-system-expat --with-system-ffi --without-dtrace --without-doc-strings"
${SUDO} /bin/bash -c "cd ${DEST_DIR}'/marsnake/Python-3.6.8' && ./configure --prefix=${CONFIGURE_PREFIX} ${CONFIGURE_PARAMS}"

if [ ! $? -eq 0 ]; then
	Display --indent 3 --text "- Configure" --result "FAILED" --color RED
        exit 1
fi

Display --indent 3 --text "- Make"
${SUDO} ${MAKE_BINARY} -C ${DEST_DIR}"/marsnake/Python-3.6.8" build_all

if [ ! $? -eq 0 ]; then
	Display --indent 3 --text "- Make" --result "FAILED" --color RED
        exit 1
fi

Display --indent 3 --text "- Make install"
${SUDO} ${MAKE_BINARY} -C ${DEST_DIR}"/marsnake/Python-3.6.8" altinstall

if [ ! $? -eq 0 ]; then
        Display --indent 3 --text "- Make install" --result "FAILED" --color RED
        exit 1
fi

#Display --indent 3 --text "- Cleaning"
#${SUDO} ${RM_BINARY} -f ${DEST_DIR}"/marsnake/lib/Python-3.6.8.tar.xz"
#${SUDO} ${RM_BINARY} -rf ${DEST_DIR}"/marsnake/Python-3.6.8"

#if [ ! $? -eq 0 ]; then
#        Display --indent 3 --text "- Clean" --result "FAILED" --color YELLOW
#fi

Display --indent 2 --text "- Installing python virtualenv"
${SUDO} ${DEST_DIR}/marsnake/interpreter_install/bin/pip3.6 install virtualenv

if [ ! $? -eq 0 ]; then
	Display --indent 2 --text "- Install python virtualenv" --result "FAILED" --color RED
	exit 1
fi

Display --indent 2 --text "- Setting up python virtualenv"
${SUDO} ${DEST_DIR}/marsnake/interpreter_install/bin/virtualenv --python=${DEST_DIR}"/marsnake/interpreter_install/bin/python3.6" ${DEST_DIR}"/marsnake/interpreter_env"

if [ ! $? -eq 0 ]; then
        Display --indent 3 --text "- Execute virtualenv" --result "FAILED" --color RED
        exit 1
fi

# enter virtualenv
${SUDO} /bin/bash -c "source ${DEST_DIR}'/marsnake/interpreter_env/bin/activate' && pip3.6 install -r ${DEST_DIR}'/marsnake/requirements.txt'"

if [ ! $? -eq 0 ]; then
	Display --indent 3 --text "- Install essential PyPI package" --result "FAILED" --color RED
	exit 1
fi

#Login to server
Display --indent 2 --text "- Registering the device"
${SUDO} /bin/bash -c "source ${DEST_DIR}'/marsnake/interpreter_env/bin/activate' && python3.6 ${DEST_DIR}'/marsnake/login.py'"

Display --indent 1 --text "- Set up Marsnake auto-start"

if [ ! ${SYSTEMCTL_BINARY} ] && [ ! ${INITCTL_BINARY} ]; then
	Display --indent 2 --text "- Get systemctl/initctl" --result "NOT FOUND" --color RED
	Display --indent 2 --text "- Marsnake auto-start disabled"

	Display --indent 1 --text "- Staring Marsnake"
	${SUDO} /bin/bash -c "source ${DEST_DIR}'/marsnake/interpreter_env/bin/activate' && python3.6 ${DEST_DIR}'/marsnake/init.py'" &

	Display --indent 1 --text "Enjoy!"
	exit 0
fi

Display --indent 2 --text "- Writing start script to /usr/share/Marsnake"

${SUDO} mkdir --parents '/usr/share/Marsnake'

if [ ! $? -eq 0 ]; then
	Display --indent 3 --text "- Create directory" --result "FAILED" --color RED
	exit 1
fi

USR_SHARE_SCRIPT="#!/bin/bash \nsource '${DEST_DIR}'/marsnake/interpreter_env/bin/activate \npython3.6 '${DEST_DIR}'/marsnake/init.py"
${SUDO} /bin/bash -c "env echo -e '${USR_SHARE_SCRIPT}' > /usr/share/Marsnake/launcher"

if [ ! $? -eq 0 ]; then
        Display --indent 3 --text "- Write script to /usr/share/Marsnake" --result "FAILED" --color RED
        exit 1
fi

${SUDO} ${CHMOD_BINARY} +x '/usr/share/Marsnake/launcher'

if [ ! $? -eq 0 ]; then
        Display --indent 3 --text "- Change script permission" --result "FAILED" --color RED
        exit 1
fi

if [ ${SYSTEMCTL_BINARY} ]; then
	Display --indent 2 --text "- Adding Marsnake service to systemd"

	SYSTEMCTL_SCRIPT='[Unit]\nDescription=Marsnake Client\nAfter=network.target\n[Service]\nEnvironment="HOME='${HOME}'"\nType=simple\nRestart=always\nWorkingDirectory='${DEST_DIR}'\nExecStart=/usr/share/Marsnake/launcher\n\n[Install]\nWantedBy=multi-user.target\n'
	${SUDO} /bin/sh -c "env echo -e '${SYSTEMCTL_SCRIPT}' > /etc/systemd/system/marsnake.service"

	if [ ! $? -eq 0 ]; then
        	Display --indent 3 --text "- Write script to /etc/systemd" --result "FAILED" --color RED
        	exit 1
	fi

	${SUDO} ${SYSTEMCTL_BINARY} enable marsnake.service

	if [ ! $? -eq 0 ]; then
                Display --indent 3 --text "- Enable marsnake service" --result "FAILED" --color RED
                exit 1
        fi

	Display --indent 1 --text "- Staring Marsnake"
	${SUDO} ${SYSTEMCTL_BINARY} daemon-reload
	${SUDO} ${SYSTEMCTL_BINARY} restart marsnake.service

	if [ ! $? -eq 0 ]; then
                Display --indent 3 --text "- Start marsnake service" --result "FAILED" --color RED
                exit 1
        fi
else
	Display --indent 2 --text "- Adding Marsnake service to Upstart"

	INITCTL_SCRIPT='# Marsnake auto-start configuration\n\nstart on stopped rc RUNLEVEL=[2345]\nstop on runlevel [!2345]\nrespawn\nenv HOME='${HOME}'\nexec /usr/share/Marsnake/launcher\n'
	${SUDO} /bin/sh -c "env echo -e '${INITCTL_SCRIPT}' > /etc/init/marsnake.conf"

	if [ ! $? -eq 0 ]; then
                Display --indent 3 --text "- Write script to /etc/init" --result "FAILED" --color RED
                exit 1
        fi

	Display --indent 2 --text "- Staring Marsnake"
	${SUDO} ${INITCTL_BINARY} start marsnake

	if [ ! $? -eq 0 ]; then
                Display --indent 3 --text "- Start marsnake service" --result "FAILED" --color RED
                exit 1
        fi
fi

Display --indent 1 --text "Enjoy!"


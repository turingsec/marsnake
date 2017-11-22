#!/bin/sh

if [ -f ${CREDENTIAL_FILE} ]; then
	RESULT=1
else
	read -p "Please enter your ${PROGRAM} cloud username: " USERNAME

	if [ ! -z ${USERNAME} ]; then
		echo ${USERNAME} > ${CREDENTIAL_FILE}
		#$(${OPENSSL_BINARY} rsautl -encrypt -in ${CREDENTIAL_FILE} -inkey ${RSA_PUBLIC_KEY} -pubin -out ${CREDENTIAL_FILE} 2> /dev/null)
		
		if [ $? -eq 0 ]; then
			RESULT=0
		else
			RESULT=2
		fi
	else
		RESULT=2
	fi
fi
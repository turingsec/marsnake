Welcome to Marsnake
===========================
Marsnake is an IT Infrastructure Security Operations Platform

|                    |                             |
|--------------------|-----------------------------|
| Supported Versions | ![Supported Versions][vi]   |

## Essential required packages
* Python Environment(Python2.7 or Python 3.6)
* python-devel
* pip
* lshw
* openssl
* gcc
* imlib2

## Essential required python modules
* rsa
* pycrypto
* psutil
* futures
* ptyprocess
* pystun
* pywinpty
* vcruntime 2015 x32 x64

## Support OS
| Distribution  | Release | Basic Info| Monitor | Vulscan | Hardening
|:----------:|:-----------:|:-----------:|:-----------:|:-----------:|:-----------:|
| Ubuntu  | 11, 12, 14, 15, 16| YES | YES | YES | YES |
| Debian  | 7, 8, 9 | YES | YES | YES | YES |
| Red Hat | 5, 6, 7 | YES | YES | YES | YES |
| CentOS | 6, 7 | YES | YES | YES | YES |
| Fedora  | 22, 23, 24, 25, 26 | YES | YES | YES | YES |
| openSUSE | 42 | YES | YES | NO | YES |
| Mint | 18.3 | YES | YES | YES | YES |
| MacOS X | 10 | YES | YES | NO | NO |

## Tutorial:
This tutorial will let you know how to install Marsnake client and how to associate your devices with cloud account
This can be done in the following steps.

1. Register a cloud account
2. Launch ./install.sh script
3. Associate your cloud account with your device
4. Enjoy

### Step1. Register a cloud account
Visit http://www.marsnake.com to register a cloud account.  
Cloud account used to manage your multiple devices via web panel.


### Step2. Launch ./install.sh script
This script help you to install Marsnake client daemon on your device.  
We recommend you to launch script with root privilege to have a better experience.  

```Bash
chmod +x install.sh
./install.sh
```


### Step3. Associate your cloud account with your device
Enter your cloud account registed on Step1


### Step4. Enjoy
You can visit http://www.marsnake.com to manage your devices

[vi]: https://img.shields.io/badge/python-2.6%2C2.7-green.svg
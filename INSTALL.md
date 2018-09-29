# Port-Ability
Modified: Saturday, September 29, 2018 7:54 AM

_Port-Ability_ is a Python 3 script, and associated files, designed to enable a simple, controlled, command-line DEV -> STAGE -> PROD development and deployment workflow for 'Dockerized' application stacks.

## Python 3 Setup

In OSX (High Sierra) following
https://stackoverflow.com/questions/47255517/brew-install-python3-didnt-install-pip3 to install Python 3.7 via Homebrew.  Install of this in September 2018 required an upgrade to XCode 10.0 and corresponding XCode Commandline Tools.  I used guidance from https://github.com/Homebrew/homebrew-core/issues/31679#issuecomment-423259873 to get it working.

## Installation

_Port_Ability_ is currently dependent on Python 3 (version 3.6 in my case). In CentOS I recommend the process documented for CentOS at https://stackoverflow.com/questions/41328451/ssl-module-in-python-is-not-available-when-installing-package-with-pip3, or for Linux in general try https://www.tecmint.com/install-python-in-linux/ to ensure that Python 3 is installed.
_Port-Ability_ is built to run from its own Python 3 'virtual environment'.  I created my virtual environment following guidance in https://docs.python.org/3/tutorial/venv.html. My command sequence in OSX (or Linux) was...

```
cd ~
git clone https://github.com/SummittDweller/Port-Ability.git
cd ~/Port-Ability
mv -f app app-backup
python3 -m venv app     # assumes 'python3' runs a Python version 3 interpreter.  Mine is version 3.6
source app/bin/activate
rsync -aruvi app-backup/. app/ --exclude=bin --exclude=include --exclude=lib --exclude=pyvenv.cfg --progress
rm -fr app-backup
cd app
curl https://bootstrap.pypa.io/get-pip.py | python3
pip install -r requirements.txt
sudo ln -s ~/Port-Ability/app/port-ability.sh /usr/local/bin/port-ability
```

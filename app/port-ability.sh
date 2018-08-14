#!/bin/bash
#
#    Modified: Tuesday, August 14, 2018 8:35 AM
#
cwd=`pwd`
cd ${HOME}/Port-Ability
source app/bin/activate
python3 app/port_ability.py $@
cd ${cwd}

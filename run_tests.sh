#!/bin/sh

SCRIPT=`readlink -f "$0"`
# Absolute path this script is in, thus /home/user/bin
SCRIPTPATH=`dirname "$SCRIPT"`

(cd $SCRIPTPATH && coverage run --source openerp_proxy -m unittest discover -v && coverage html -d coverage)

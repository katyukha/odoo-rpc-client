#!/bin/sh

SCRIPT=`readlink -f "$0"`
# Absolute path this script is in, thus /home/user/bin
SCRIPTPATH=`dirname "$SCRIPT"`

(cd $SCRIPTPATH && rm .coverage && coverage run --source openerp_proxy -m unittest -v openerp_proxy.tests.all && coverage html -d coverage)

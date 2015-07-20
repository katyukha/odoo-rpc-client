#!/bin/sh

SCRIPT=`readlink -f "$0"`
# Absolute path this script is in, thus /home/user/bin
SCRIPTPATH=`dirname "$SCRIPT"`

(cd $SCRIPTPATH && nosetests --with-coverage --cover-html --cover-html-dir=coverage --cover-package=openerp_proxy.* -v )

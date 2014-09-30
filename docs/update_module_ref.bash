#!/bin/bash

# Guess directory script is placed in
F=`readlink -f $0`
BASEDIR=`dirname $F`

(cd $BASEDIR &&
    python generate_modules.py -d source/module_ref/ -n 'OpenERP Proxy' -s 'rst' $@ ../openerp_proxy)

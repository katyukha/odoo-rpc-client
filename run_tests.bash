#!/bin/bash

SCRIPT=`readlink -f "$0"`
# Absolute path this script is in, thus /home/user/bin
SCRIPTPATH=`dirname "$SCRIPT"`

(cd $SCRIPTPATH && \
    virtualenv venv_test && \
    source ./venv_test/bin/activate && \
    pip install --upgrade pip setuptools coverage mock pudb ipython && \
    python setup.py develop && \
    rm -f .coverage && \
    coverage run --source openerp_proxy -m unittest -v openerp_proxy.tests.all && \
    coverage html -d coverage && \
    deactivate && \
    rm -rf venv_test)

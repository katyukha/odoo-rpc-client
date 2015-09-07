#!/bin/bash

SCRIPT=`readlink -f "$0"`
# Absolute path this script is in, thus /home/user/bin
SCRIPTPATH=`dirname "$SCRIPT"`

TEST_MODULE=${TEST_MODULE:-'openerp_proxy.tests.all'};
PY_VERSIONS=${PY_VERSIONS:-"2.7 3.4"};

function test_it {
    local py_version=$1;
    (cd $SCRIPTPATH && \
                virtualenv venv_test -p python${py_version} && \
                source ./venv_test/bin/activate && \
                pip install --upgrade pip setuptools coverage mock pudb ipython[notebook] simple-crypt && \
                python setup.py develop && \
                rm -f .coverage && \
                coverage run --source openerp_proxy -m unittest -v $TEST_MODULE && \
                coverage html -d coverage && \
                deactivate && \
                rm -rf venv_test)
}

function main {
    for version in $PY_VERSIONS; do
        test_it $version;
    done
}

main;

#!/bin/bash

# simple script to run tests on dev machine for few python versions (by default 2.7, 3.4)
# This script will automatically create separate virtual environment for each test.
# 
# Following environment variables could be used to configure test run:
#   - TEST_MODULE - python module name to look for test cases in
#                   (default: openerp_proxy.tests.all)
#   - PY_VERSIONS - string that contains space separated python versions to test app on


SCRIPT=`readlink -f "$0"`
SCRIPTPATH=`dirname "$SCRIPT"`  # directory that contains this script

TEST_MODULE=${TEST_MODULE:-'openerp_proxy.tests.all'};
PY_VERSIONS=${PY_VERSIONS:-"2.7 3.4"};


# run_single_test <python version>
function run_single_test {
    local py_version=$1;
    (cd $SCRIPTPATH && \
                virtualenv venv_test -p python${py_version} && \
                source ./venv_test/bin/activate && \
                pip install --upgrade pip setuptools coverage mock pudb ipython[notebook] simple-crypt && \
                python setup.py develop && \
                coverage run -p -m unittest -v $TEST_MODULE && \
                deactivate && \
                rm -rf venv_test
    )
}

function main {
    rm -f .coverage;

    for version in $PY_VERSIONS; do
        run_single_test $version;
    done
    coverage combine;
    coverage html -d coverage;
    rm .coverage;
}

main;

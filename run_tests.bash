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

usage="
    Usage:

        run_tests.bash [--py-version v1] [--py-version v2] [--with-extensions] [--with-db] [--test-module <module>]

"
        

# process cmdline options
while [[ $# -gt 0 ]]
do
    key="$1";
    case $key in
        -h|--help|help)
            echo "$usage";
            exit 0;
        ;;
        --py-version)
            PY_VERSIONS="$PY_VERSIONS $2";
            shift;
        ;;
        --with-extensions)
            export TEST_WITH_EXTENSIONS=1;
        ;;
        --with-db)
            export TEST_DB_SERVICE=1;
        ;;
        --test-module)
            TEST_MODULE="$2";
            shift;
        ;;
        *)
            echo "Unknown option $key";
            exit 1;
        ;;
    esac
    shift
done


# config defaults
PY_VERSIONS=${PY_VERSIONS:-"2.7 3.4"};


if [ ! -z $TEST_MODULE ]; then
    TEST_MODULE_OPT=" --test-suite=$TEST_MODULE";
fi

# run_single_test <python version>
function run_single_test {
    local py_version=$1;
    (cd $SCRIPTPATH && \
                virtualenv --no-site-packages -p python${py_version} venv_test&& \
                source ./venv_test/bin/activate && \
                pip install --upgrade pip setuptools pbr && \
                pip install --upgrade coverage six extend_me requests mock pudb ipython[notebook] && \
                coverage run -p setup.py test $TEST_MODULE_OPT && \
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

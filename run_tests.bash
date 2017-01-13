#!/bin/bash

# simple script to run tests on dev machine for few python versions (by default 2.7, 3.4)
# This script will automatically create separate virtual environment for each test.
# 
# Following environment variables could be used to configure test run:
#   - TEST_MODULE - python module name to look for test cases in
#                   (default: odoo_rpc_client.tests.all)
#   - PY_VERSIONS - string that contains space separated python versions to test app on



SCRIPT=`readlink -f "$0"`
SCRIPTPATH=`dirname "$SCRIPT"`  # directory that contains this script

usage="
    Usage:

        run_tests.bash [options]
    Available options:
        --py-version v1         - use specific python version. may be present multiple times
        --with-db               - perform database related tests (create, dump, drop, restore)
        --recreate-db           - recreate test database at start
        --test-module <module>  - run specific test suit (python module that contains test cases)
        --reuse-venv            - do not delete/recreate virtual environment used for test
        --flake8                - Run flake 8 on project's code

"

# Hide deprecation warnings of IPython, highly logged when testing on Python3.5
export PYTHONWARNINGS="ignore::DeprecationWarning:IPython"

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
        --with-db)
            export TEST_DB_SERVICE=1;
        ;;
        --recreate-db)
            export RECREATE_DB=1;
        ;;
        --test-module)
            TEST_MODULE="$2";
            shift;
        ;;
        --flake8)
            TEST_FLAKE8=1
        ;;
        --reuse-venv)
            REUSE_VENV=1;
        ;;
        *)
            echo "Unknown option $key";
            exit 1;
        ;;
    esac
    shift
done


set -e    # fail on any error


# config defaults
PY_VERSIONS=${PY_VERSIONS:-"2.7 3.5"};


if [ ! -z $TEST_MODULE ]; then
    TEST_MODULE_OPT=" --test-suite=$TEST_MODULE";
fi

function run_flake_8 {
    if [ ! -z $TEST_FLAKE8 ]; then
        flake8 --count --statistics odoo_rpc_client;
    fi
}

# run_single_test <python version>
function run_single_test {
    local py_version=$1;
    local workdir=`pwd`;

    echo "Saving current work directory $workdir and moving into $SCRIPTPATH";

    cd $SCRIPTPATH;

    local venv_name="venv_test_${py_version}";

    # Check if we need to create virtual environment
    if [ ! -d "$venv_name" ] || [ -z $REUSE_VENV ]; then
        virtualenv --no-site-packages -p python${py_version} $venv_name

        # mark that virtualenv was created and we need to install here packages
        local venv_created=1;
    fi

    source ./$venv_name/bin/activate

    # if virtualenv was [re]created then we need to install packages
    if [ ! -z $venv_created ]; then
        pip install --upgrade pip setuptools pbr flake8
        pip install --upgrade coverage six extend_me requests mock anyfield
    fi

    # install in develop mode
    python setup.py develop

    set +e   # allow errors

    # Run tests
    run_flake_8 && \
        coverage run -p setup.py test $TEST_MODULE_OPT
    res=$?;  # save test results

    set -e   # disallow errors

    deactivate  # deactivate test environment

    # and if not plan to reuse this environment, we have to delete it
    if [ -z $REUSE_VENV ]; then
        rm -rf $venv_name
    fi

    # go back to work directory
    echo "Going back to work directory $workdir";
    cd $workdir;

    return $res;
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

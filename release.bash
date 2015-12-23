#!/bin/bash


SCRIPT=`readlink -f "$0"`
SCRIPTPATH=`dirname "$SCRIPT"`  # directory that contains this script

VENV_PY_2_DIR=$SCRIPTPATH/venv_py2;
VENV_PY_3_DIR=$SCRIPTPATH/venv_py3;

USE_PY_VERSION="python3"

usage="
    Usage:

        release.bash [options]

    Available options:
        -n|--dry-run           - do not do release, just build doc, and build packages
        --py2                  - use python 2
        --py3                  - use python 3 (default)

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
        -n|--dry-run)
            DRY_RUN=1;
        ;;
        --py2)
            USE_PY_VERSION='python2';
        ;;
        --py3)
            USE_PY_VERSION='python3';
        ;;
        *)
            echo "Unknown option $key";
            exit 1;
        ;;
    esac
    shift
done


set -e    # fail on any error

# make_venv <python-version> <dest dir>
function make_venv {
    local py_version=$1;
    local dest_dir=$2;

    if [ -d $dest_dir ]; then
        echo "Removing dest dir '$dest_dir'...";
        rm -rf $dest_dir;
    fi

    virtualenv -p $py_version $dest_dir;
    $dest_dir/bin/easy_install --upgrade setuptools pip;
}

function build_docs {
    pip install --upgrade sphinx[all];
    (cp -f $SCRIPTPATH/README.rst $SCRIPTPATH/docs/source/intro.rst && cd $SCRIPTPATH/docs && make html)
}

function release_implementation {
    # install this project in virtual environment
    python $SCRIPTPATH/setup.py develop

    # Build options. if no dry run, then upload to pypi
    local setup_options=" sdist bdist_wheel ";
    if [ -z $DRY_RUN ]; then
        setup_options="$setup_options upload";
    fi

    # Build [and upload to pypi] project
    python $SCRIPTPATH/setup.py $setup_options;

    build_docs;

    if [ -z $DRY_RUN ]; then
        python setup.py upload_docs --upload-dir $SCRIPTPATH/docs/build/html/;
    fi
}

function release_python_2 {
    local py_version=python2;
    local venv_dir=$VENV_PY_2_DIR;

    make_venv $py_version $venv_dir;

    source $venv_dir/bin/activate;
    release_implementation;
    deactivate;

    rm -r $venv_dir;
}

function release_python_3 {
    local py_version=python3;
    local venv_dir=$VENV_PY_3_DIR;

    make_venv $py_version $venv_dir;

    source $venv_dir/bin/activate;
    release_implementation;
    deactivate;

    rm -r $venv_dir;
}

function do_release {
    if [ "$USE_PY_VERSION" == "python3" ]; then
        release_python_3;
    elif [ "$USE_PY_VERSION" == "python2" ]; then
        release_python_2;
    else
        echo "Error";
    fi
}

do_release;

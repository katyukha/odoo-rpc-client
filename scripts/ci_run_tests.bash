#!/bin/bash

set -e;  # fail on any error

if [ ${ODOO_VERSION} != "7.0" ]; then
  ODOO_TEST_PROTOCOL='json-rpc' coverage run -p setup.py test;
fi

ODOO_TEST_PROTOCOL='xml-rpc' coverage run -p setup.py test;
coverage combine;

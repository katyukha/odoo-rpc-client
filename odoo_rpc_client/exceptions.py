# -*- coding: utf-8 -*-
# Copyright © 2014-2018 Dmytro Katyukha <dmytro.katyukha@gmail.com>

#######################################################################
# This Source Code Form is subject to the terms of the Mozilla Public #
# License, v. 2.0. If a copy of the MPL was not distributed with this #
# file, You can obtain one at http://mozilla.org/MPL/2.0/.            #
#######################################################################


class Error(Exception):
    """ Base class for exceptions"""
    pass


class ConnectorError(Error):
    """ Base class for exceptions related to connectors """
    pass


class ClientException(Error):
    """ Base class for client related exceptions
    """
    pass


class ReportError(Error):
    """ Error raise in process of report generation
    """
    pass


class LoginException(ClientException):
    """ This exception should be raised, when operations requires
        login and password. For example interaction with Odoo object service.
    """
    pass


class ObjectException(ClientException):
    """ Base class for exceptions related to Objects """
    pass

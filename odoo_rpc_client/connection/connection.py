# -*- coding: utf-8 -*-
# Copyright © 2014-2018 Dmytro Katyukha <dmytro.katyukha@gmail.com>

#######################################################################
# This Source Code Form is subject to the terms of the Mozilla Public #
# License, v. 2.0. If a copy of the MPL was not distributed with this #
# file, You can obtain one at http://mozilla.org/MPL/2.0/.            #
#######################################################################

import six
from extend_me import ExtensibleByHashType

DEFAULT_TIMEOUT = None

__all__ = ('get_connector', 'get_connector_names', 'ConnectorBase')

ConnectorType = ExtensibleByHashType._('Connector', hashattr='name')


def get_connector(name):
    """ Return connector specified by it's name
    """
    return ConnectorType.get_class(name)


def get_connector_names():
    """ Returns list of connector names registered in system
    """
    return ConnectorType.get_registered_names()


class ConnectorBase(six.with_metaclass(ConnectorType)):
    """ Base class for all connectors

        :param str host: hostname to connect to
        :param int port: port to connect to
        :param dict extra_args: extra arguments for specific connector.
    """

    def __init__(self, host, port, timeout=DEFAULT_TIMEOUT, extra_args=None):
        self._host = host
        self._port = port
        self._timeout = timeout
        self._extra_args = {} if extra_args is None else extra_args

        self.__services = {}

    @property
    def host(self):
        """ Connector host
        """
        return self._host

    @property
    def port(self):
        """ Connector port
        """
        return self._port

    @property
    def timeout(self):
        """ Connector timeout
        """
        return self._timeout

    @property
    def extra_args(self):
        """ Connector extra arguments
        """
        return self._extra_args

    def update_extra_args(self, **kwargs):
        """ Update extra args and clean service cache
        """
        self.extra_args.update(kwargs)
        self.__services = {}

    def _get_service(self, name):  # pragma: no cover
        raise NotImplementedError

    def get_service(self, name):
        """ Returns service for specified *name*

            :param name: name of service
            :return: specified service instance
        """
        service = self.__services.get(name, None)
        if service is None:
            service = self._get_service(name)
            self.__services[name] = service

        return service

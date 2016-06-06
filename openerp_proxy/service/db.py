import six
import time
from pkg_resources import parse_version

from ..service.service import ServiceBase

__all__ = ('DBService',)


def to_dbname(db):
    """ Converts db to string, that represents database name

        :param db: Client instance or string with name of database
        :type db: Client|str
        :return: string with database name
        :rtype: str
        :raises ValueError: value of db is not parsable
    """
    from openerp_proxy.core import Client
    if isinstance(db, six.string_types):
        return db
    elif isinstance(db, Client) and db.dbname is not None:
        return db.dbname
    else:
        raise ValueError("Wrong value for db!")


class DBService(ServiceBase):
    """ Service class to simplify interaction with 'db' service
    """
    class Meta:
        name = 'db'

    def list_db(self):
        """ Display list of databses of thist connection
        """
        return self._service.list()

    def create_db(self, password, dbname, demo=False, lang='en_US',
                  admin_password='admin'):
        """ Create new database on server, named *dbname*

            :param str password: super admin password
            :param str dbname: name of database to create
            :param bool demo: load demo data or not. Default: False
            :param str lang: language to be used for database. Default: 'en_US'
            :param str admin_password: password to be used for 'Administrator'
                                       database user.
                                       Default: 'admin'
            :return: Client instance logged to created database as admin user.
            :rtype: instance of *openerp_proxy.core.Client*
        """
        from openerp_proxy.core import Client

        # requires server version >= 6.1
        if self.server_version() >= parse_version('6.1'):
            self.create_database(password, dbname, demo, lang, admin_password)
        else:  # pragma: no cover
            # for other server versions
            process_id = self.create(password, dbname, demo, lang,
                                     admin_password)

            # wait while database will be created
            while self.get_process(process_id)[0] < 1.0:
                time.sleep(1)

        client = Client(self.client.host, port=self.client.port,
                        protocol=self.client.protocol, dbname=dbname,
                        user='admin', pwd=admin_password)
        return client

    def drop_db(self, password, db):
        """ Drop specified database

            :param str password: super admin password
            :param str|Client db: name of database or *Client* instance
                                  with *client.dbname is not None*
            :raise: `ValueError` (unsupported value of *db* argument)
        """
        return self.drop(password, to_dbname(db))

    def dump_db(self, password, db, **kwargs):
        """ Dump database

            Note, that from defined arguments, may be passed other arguments
            (for example odoo version 9.0 requires format arg to be passed)

            :param str password: super admin password
            :param str|Client db: name of database or *Client* instance
                                  with *client.dbname is not None*
            :param str format: (only odoo 9.0) (default: zip)
            :raise: `ValueError` (unsupported value of *db* argument)
            :return: bytestring with base64 encoded data
            :rtype: bytes
        """
        # format argument available only for odoo version 9.0
        #
        # Note, checking for 9.0rc because Odoo changed version naming.
        # See issue https://github.com/odoo/odoo/issues/9799
        #
        if self.server_version() >= parse_version('9.0rc'):
            args = [kwargs.get('format', 'zip')]
        else:
            args = []

        dump_data = self.dump(password, to_dbname(db), *args).encode()

        return dump_data

    def restore_db(self, password, dbname, data, **kwargs):
        """ Restore database

            :param str password: super admin password
            :param str dbname: name of database
            :param bytes data: restore data (base64 encoded string)
            :param bool copy: (only odoo 8.0+) if set to True,
                              then new db-uid will be generated.
                              (default: False)
            :return: True
            :rtype: bool
        """
        assert isinstance(data, bytes), \
            "data must be instance of bytes. got: %s" % type(data)
        if self.server_version() >= parse_version('8.0') and 'copy' in kwargs:
            args = [kwargs['copy']]
        else:
            args = []

        return self.restore(password, dbname, data.decode(), *args)

    def server_version(self):
        """ Returns server version.

            (Already parsed with pkg_resources.parse_version)
        """
        return parse_version(self.server_version_str())

    def server_version_str(self):
        """ Return server version (not wrapped by pkg.parse_version)
        """
        return self._service.server_version()

    # make able to check if there some databases on server exists
    def __contains__(self, name):
        return name in self.list_db()

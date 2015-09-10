import time
from pkg_resources import parse_version

from openerp_proxy.service.service import ServiceBase


class DBService(ServiceBase):
    """ Service class to simplify interaction with 'db' service
    """
    class Meta:
        name = 'db'

    def list_db(self):
        """ Display list of databses of thist connection
        """
        return self._service.list()

    def create_db(self, password, dbname, demo=False, lang='en_US', admin_password='admin'):
        """ Create new database on server, named *dbname*

            :param str password: super admin password
            :param str dbname: name of database to create
            :param bool demo: load demo data or not. Default: False
            :param str lang: language to be used for database. Default: 'en_US'
            :param str admin_password: password to be used for 'Administrator' database user.
                                       Default: 'admin'
            :return: Client instance logged to created database as admin user.
            :rtype: instance of *openerp_proxy.core.Client*
        """
        from openerp_proxy.core import Client

        # requires server version >= 6.1
        if self.server_version() >= parse_version('6.1'):
            self.create_database(password, dbname, demo, lang, admin_password)
        else:  # for other server versions
            process_id = self.create(password, dbname, demo, lang, admin_password)

            # wait while database will be created
            while self.get_process(process_id)[0] < 1.0:
                time.sleep(1)

        client = Client(self.proxy.host, port=self.proxy.port,
                        protocol=self.proxy.protocol, dbname=dbname,
                        user='admin', pwd=admin_password)
        return client

    def drop_db(self, password, db):
        """ Drop specified database

            :param str password: super admin password
            :param str|Client db: name of database or *Client* instance
                                  with *client.dbname is not None* name secified
            :raise: `ValueError` (unsupported value of *db* argument)
        """
        from openerp_proxy.core import Client
        if isinstance(db, basestring):
            dbname = db
        elif isinstance(db, Client) and db.dbname is not None:
            dbname = db.dbname
        else:
            raise ValueError("Wrong value for db!")

        return self.drop(password, dbname)

    def server_version(self):
        """ Returns server version.

            (Already parsed with pkg_resources.parse_version)
        """
        return parse_version(self._service.server_version())

    # make able to check if there some databases on server exists
    def __contains__(self, name):
        return name in self.list_db()

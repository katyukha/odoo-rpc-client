from openerp_proxy.service.service import ServiceBase


class DBService(ServiceBase):
    """ Service class to simplify interaction with 'db' service
    """
    class Meta:
        name = 'db'

    def list_db(self):
        """ Display list of databses of thist connection
        """
        return self.list()

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
        self.create(password, dbname, demo, lang, admin_password)
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
        if isinstance(db, basestring):
            dbname = db
        elif isinstance(db, Client) and db.dbname is not None:
            dbname = db.dbname
        else:
            raise ValueError("Wrong value for db!")

        return self.drop(password, dbname)

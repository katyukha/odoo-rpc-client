import json
import os.path
import pprint
from getpass import getpass

# project imports
from core import ERP_Proxy
from plugin import ERP_PluginManager


__all__ = ('ERP_Session',)


class ERP_Session(object):

    """ Simple session manager which allows to manage databases easier
        This class stores information about databases You used in home
        directory, and on init it loads history and allows simply connect
        to database by url or index. No more hosts, usernames, ports, etc...
        required to be memorized.
        Just on session start call:

            >>> print session

        And You will get all databases You worked with listed as (index, url) pairs.
        to connect to one of thouse databases just call session[index|url] and required
        ERP_Proxy object will be returned.
    """

    def __init__(self, data_file='~/.openerp_proxy.json'):
        self.data_file = os.path.expanduser(data_file)
        self._databases = {}  # key: url; value: instance of DB or dict with init args

        if os.path.exists(self.data_file):
            with open(self.data_file, 'rt') as json_data:
                data = json.load(json_data)
                if data.get('databases', False) is not False:  # For compatability with older versions
                    self._databases = data['databases']
                    for plugin_name, plugin_path in data.get('plugins', {}).iteritems():
                        try:
                            self.load_plugin(plugin_path)
                        except Exception:
                            # TODO: implement some notifications about errors
                            # on plugin loading
                            pass
                else:
                    self._databases = data  # For compatability with older versions

        self._db_index = {}  # key: index; value: url
        self._db_index_rev = {}  # key: url; value: index
        self._db_index_counter = 0

    def load_plugin(self, path):
        # TODO: think about ability to pass here plugin name as argument
        #       it may be useful for saving in session.
        ERP_PluginManager.load_plugin(path)

    @property
    def index(self):
        """ Property which returns dict with {index: url}
        """
        if not self._db_index:
            for url in self._databases.keys():
                self._index_url(url)
        return dict(self._db_index)

    def _index_url(self, url):
        """ Returns index of specified URL, or adds it to
            store assigning new index
        """
        if self._db_index_rev.get(url, False):
            return self._db_index_rev[url]

        self._db_index_counter += 1
        self._db_index[self._db_index_counter] = url
        self._db_index_rev[url] = self._db_index_counter
        return self._db_index_counter

    def _add_db(self, url, db):
        """ Add database to history
        """
        self._databases[url] = db
        self._index_url(url)

    def get_db(self, url_or_index):
        """ Returns instance of ERP_Proxy object, that represents single
            OpenERP database it connected to, specified by passed index (integer) or
            url (string) of database, previously saved in session.

            @param url_or_index: must be integer (if index) or string (if url). this parametr
                                 specifies database to get from session
            @return: ERP_Proxy instance
        """
        if isinstance(url_or_index, (int, long)):
            url = self._db_index[url_or_index]
        else:
            url = url_or_index

        db = self._databases.get(url, False)
        if not db:
            raise ValueError("Bad url %s. not found in history nor databases" % url)

        if isinstance(db, ERP_Proxy):
            return db

        db = ERP_Proxy(pwd=getpass('Password: '), **db)
        # injecting Plugins:
        db.plugins = ERP_PluginManager(db)
        # Plugins injected
        self._add_db(url, db)
        return db

    @property
    def db_list(self):
        """ Returns list of URLs of databases available in current session
        """
        return self._databases.keys()

    def connect(self, dbname=None, host=None, user=None, pwd=None, port=8069, protocol='xml-rpc', verbose=False):
        """ Wraper aroun ERP_Proxy constructor class to simplify connect from shell.

            @param dbname: name of database to connect to (will be asked interactvely if not provided)
            @param host: host name to connect to (will be asked interactvely if not provided)
            @param user: user name to connect as (will be asked interactvely if not provided)
            @param pwd: password for selected user (will be asked interactvely if not provided)
            @param port: port to connect to. (default: 8069)
            @param verbose: to be verbose, or not to be. (default: False)
            @return: ERP_Proxy object
        """
        host = host or raw_input('Server Host: ')
        dbname = dbname or raw_input('Database name: ')
        user = user or raw_input('ERP Login: ')
        pwd = pwd or getpass("Password: ")

        url = "%(protocol)s://%(user)s@%(host)s:%(port)s/%(database)s" % dict(user=user,
                                                                              host=host,
                                                                              database=dbname,
                                                                              port=port,
                                                                              protocol=protocol)
        db = self._databases.get(url, False)
        if isinstance(db, ERP_Proxy):
            return db

        db = ERP_Proxy(dbname=dbname, host=host, user=user, pwd=pwd, port=port, protocol=protocol, verbose=verbose)
        self._add_db(url, db)
        return db

    def save(self):
        """ Saves session on disc
        """
        databases = {}
        for url, database in self._databases.iteritems():
            if isinstance(database, ERP_Proxy):
                init_args = {
                    'dbname': database.dbname,
                    'host': database.host,
                    'port': database.port,
                    'user': database.user,
                    'protocol': database.protocol,
                    'verbose': database.verbose,
                }
            else:
                init_args = database
            assert isinstance(init_args, dict), "init_args must be instance of dict"
            databases[url] = init_args

        plugins = ERP_PluginManager.get_plugins_info()
        data = {
            'databases': databases,
            'plugins': plugins
        }

        with open(self.data_file, 'wt') as json_data:
            json.dump(data, json_data, indent=4)

    def __getitem__(self, url_or_index):
        return self.get_db(url_or_index)

    def __str__(self):
        return pprint.pformat(self.index)

    def __repr__(self):
        return pprint.pformat(self.index)

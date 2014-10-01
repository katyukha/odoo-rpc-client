import json
import os.path
import sys
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
        self._db_aliases = {}  # key: aliase name; value: url

        self._db_index = {}  # key: index; value: url
        self._db_index_rev = {}  # key: url; value: index
        self._db_index_counter = 0

        self._start_up_imports = []   # list of modules/packages to be imported at startup

        self._extra_paths = set()

        if os.path.exists(self.data_file):
            with open(self.data_file, 'rt') as json_data:
                data = json.load(json_data)
                self._init_databases(data)
                self._init_paths(data)
                self._init_aliases(data)
                self._init_start_up_imports(data)

    def _init_databases(self, data):
        """ Initializes databases from passed data.

            @param data: dictionary with data read from saved session file
        """
        if data.get('databases', False) is not False:  # For compatability with older versions
            self._databases = data['databases']
        else:
            self._databases = data  # For compatability with older versions

    def _init_aliases(self, data):
        """ Loads db aliases saved in previous session

            @param data: dictionary with data read from saved session file
        """
        self._db_aliases = data.get('aliases', {})

    def _init_start_up_imports(self, data):
        """ Loads list of modules/packages names to be imported at start-up,
            saved in previous session

            @param data: dictionary with data read from saved session file
        """
        self._start_up_imports += data.get('start_up_imports', [])
        for i in self._start_up_imports:
            try:
                __import__(i)
            except ImportError:
                # TODO: implement some logging
                pass

    def _init_paths(self, data):
        """ This method initializes aditional python paths saved in session
        """
        for path in data.get('extra_paths', []):
            self.add_path(path)

    def add_path(self, path):
        """ Adds extra path to python import path.

            Note: this way path will be saved in session
        """
        if path not in sys.path:
            sys.path.append(path)
            self._extra_paths.add(path)

    @property
    def aliases(self):
        return self._db_aliases.copy()

    def aliase(self, name, val):
        """ Sets up aliase 'name' for val, where val
            could be index, url or ERP_Proxy object

            @return: val
        """
        if val in self._databases:
            self._db_aliases[name] = val
        elif val in self.index:
            self._db_aliases[name] = self.index[val]
        elif isinstance(val, ERP_Proxy):
            self._db_aliases[name] = val.get_url()
        else:
            raise ValueError("Bad value type")

        return val

    @property
    def index(self):
        """ Property which returns dict with {index: url}
        """
        if not self._db_index:
            for url in self._databases.keys():
                self._index_url(url)
        return dict(self._db_index)

    @property
    def start_up_imports(self):
        return self._start_up_imports

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

    def get_db(self, url_or_index, **kwargs):
        """ Returns instance of ERP_Proxy object, that represents single
            OpenERP database it connected to, specified by passed index (integer) or
            url (string) of database, previously saved in session.

            @param url_or_index: must be integer (if index) or string (if url). this parametr
                                 specifies database to get from session
            @param kwargs: can contain aditional arguments to be passed on init of ERP_Proxy
            @return: ERP_Proxy instance
        """
        if isinstance(url_or_index, (int, long)):
            url = self.index[url_or_index]
        else:
            url = self._db_aliases.get(url_or_index, url_or_index)

        db = self._databases.get(url, False)
        if not db:
            raise ValueError("Bad url %s. not found in history or databases" % url)

        if isinstance(db, ERP_Proxy):
            return db

        ep_args = db.copy()  # DB here is instance of dict
        ep_args.update(**kwargs)

        # Check password, if not provided - ask
        # TODO: implement correct behavior for IPython notebooks
        if 'pwd' not in ep_args:
            ep_args['pwd'] = getpass('Password: ')

        db = ERP_Proxy(**ep_args)
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

    def connect(self, dbname=None, host=None, user=None, pwd=None, port=8069, protocol='xml-rpc', verbose=False, no_save=False):
        """ Wraper aroun ERP_Proxy constructor class to simplify connect from shell.

            @param dbname: name of database to connect to (will be asked interactvely if not provided)
            @param host: host name to connect to (will be asked interactvely if not provided)
            @param user: user name to connect as (will be asked interactvely if not provided)
            @param pwd: password for selected user (will be asked interactvely if not provided)
            @param port: port to connect to. (default: 8069)
            @param verbose: to be verbose, or not to be. (default: False)
            @param no_save: if set to True database will not be saved to session
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
        db._no_save = no_save   # disalows saving database connection in session
        return db

    def _get_db_init_args(self, database):
        if isinstance(database, ERP_Proxy):
            return {
                'dbname': database.dbname,
                'host': database.host,
                'port': database.port,
                'user': database.user,
                'protocol': database.protocol,
                'verbose': database.verbose,
            }
        elif isinstance(database, dict):
            return database
        else:
            raise ValueError("Bad database instance. It should be dict or ERP_Proxy object")

    def save(self):
        """ Saves session on disc
        """
        databases = {}
        for url, database in self._databases.iteritems():
            if not getattr(database, '_no_save', False):
                init_args = self._get_db_init_args(database)
                databases[url] = init_args

        data = {
            'databases': databases,
            'extra_paths': list(self._extra_paths),
            'aliases': self._db_aliases,
            'start_up_imports': self._start_up_imports,
        }

        with open(self.data_file, 'wt') as json_data:
            json.dump(data, json_data, indent=4)

    def __getitem__(self, url_or_index):
        try:
            res = self.get_db(url_or_index)
        except ValueError as e:
            raise KeyError(e.message)
        return res

    def __getattr__(self, name):
        try:
            res = self.get_db(name)
        except ValueError as e:
            raise AttributeError(e.message)
        return res

    def __str__(self):
        return pprint.pformat(self.index)

    def __dir__(self):
        res = dir(super(ERP_Session, self))
        res += self.aliases.keys()
        return res

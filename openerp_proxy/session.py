import json
import os.path
import pprint
import imp

# project imports
from core import ERP_Proxy

# TODO: terminology: Util - > PlugIn


class UtilInitError(Exception):
    pass


class ERP_Utils(object):
    """ Class to hold information about utils (scripts which can be placed
        anywhere but also could be easiely connected to session and be used)
    """
    def __init__(self, erp_proxy, util_classes):
        """ @param erp_proxy: ERP_Proxy object to bind utils set to
            @param util_classes: dict with {util_name: util_class}

            # NOTE: util classes should be a reference to dict saved in session
            # for example. this allows this dict to be updated from session and
            # all changes from session will be reflected here allowing to add
            # new utils dynamically.
        """
        self.__erp_proxy = erp_proxy
        self.__util_classes = util_classes
        self.__utils = {}

    def __getitem__(self, name):
        util = self.__utils.get(name, False)
        if util is False:
            util_cls = self.__util_classes[name]
            try:
                util = util_cls(self.__erp_proxy)
            except Exception as exc:
                raise UtilInitError(exc)
            self.__utils[name] = util
        return util

    def __getattribute__(self, name):
        try:
            return super(ERP_Utils, self).__getattribute__(name)
        except AttributeError:
            try:
                return self[name]
            except KeyError:
                raise AttributeError(name)

    def __dir__(self):
        return self.__util_classes.keys()


class ERP_Session(object):

    """ Simple session manager which allows to manage databases easier
        This class stores information about databases You used in home
        directory, and on init it loads history and allows simply connect
        to database by url or index. No more hosts, usernames, ports, etc...
        required to be memorized.
        Just on session start call:
            print session
        And You will get all databases You worked with listed as (index, url) pairs.
        to connect to one of thouse databases just call session[index|url] and required
        ERP_Proxy object will be returned.
    """

    def __init__(self, data_file='~/.erp_proxy.json'):
        self.data_file = os.path.expanduser(data_file)
        self._databases = {}  # key: url; value: instance of DB or dict with init args

        if os.path.exists(self.data_file):
            with open(self.data_file, 'rt') as json_data:
                self._databases = json.load(json_data)

        self._db_index = {}  # key: index; value: url
        self._db_index_rev = {}  # key: url; value: index
        self._db_index_counter = 0

        self._util_classes = {}

    def load_util(self, path):
        """ Loads utils from specified path, which should be a python module
            or python package (not tested yet) which defines function
            'erp_proxy_plugin_init' which should return dictionary with
            key 'utils' which points to list of utility classes. each class must have
            class level attribute _name which will be used to access it from session
            or db objects. So as masic example util module may look like:

                class MyUtil(object):
                    _name = 'my_util'

                    def __init__(self, db):  # db is required argument passed by infrastructure
                        self.db = db

                    ...

                def erp_proxy_plugin_init():
                    return {'utils': [MyUtil]}
        """
        # TODO: Add ability to save utils files used in conf.
        name = os.path.splitext(os.path.basename(path))[0]
        module_name = '%s' % name
        module = imp.load_source(module_name, path)
        plugin_data = module.erp_proxy_plugin_init()
        for cls in plugin_data.get('utils', []):
            self._util_classes[cls._name] = cls

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

        db = ERP_Proxy(**db)
        # injecting utils:
        db.utils = ERP_Utils(db, self._util_classes)
        # utils injected
        self._add_db(url, db)
        return db

    @property
    def db_list(self):
        """ Returns list of URLs of databases available in current session
        """
        return self._databases.keys()

    def connect(self, dbname=None, host=None, user=None, pwd=None, port=8069, verbose=False):
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

        url = "%(user)s@%(host)s:%(port)s/%(database)s" % dict(user=user,
                                                               host=host,
                                                               database=dbname,
                                                               port=port)
        db = self._databases.get(url, False)
        if isinstance(db, ERP_Proxy):
            return db

        db = ERP_Proxy(dbname=dbname, host=host, user=user, pwd=pwd, port=port, verbose=verbose)
        self._add_db(url, db)
        return db

    def save(self):
        """ Saves session on disc
        """
        data = {}
        for url, database in self._databases.iteritems():
            if isinstance(database, ERP_Proxy):
                init_args = {
                    'dbname': database.dbname,
                    'host': database.host,
                    'port': database.port,
                    'user': database.user,
                    'verbose': database.verbose,
                }
            else:
                init_args = database
            assert isinstance(init_args, dict), "init_args must be instance of dict"
            data[url] = init_args

        with open(self.data_file, 'wt') as json_data:
            json.dump(data, json_data)

    def __getitem__(self, url_or_index):
        return self.get_db(url_or_index)

    def __str__(self):
        return pprint.pformat(self.index)

    def __repr__(self):
        return pprint.pformat(self.index)

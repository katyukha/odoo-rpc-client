import numbers
import os.path
import sys
import pprint
from getpass import getpass
from extend_me import Extensible

# project imports
from .core import Client
from .utils import (json_read,
                    json_write,
                    xinput,
                    DirMixIn)


__all__ = ('Session',)


class SessionClientExt(Client):
    """ Simple Client extension to add attribute '_no_save'
        used in session
    """
    def __init__(self, *args, **kwargs):
        super(SessionClientExt, self).__init__(*args, **kwargs)
        self._no_save = False


class Session(Extensible, DirMixIn):

    """ Simple session manager which allows to manage databases easier
        This class stores information about databases You used in home
        directory, and on init it loads history and allows simply connect
        to database by url or index. No more hosts, usernames, ports, etc...
        required to be memorized.
        Just on session start call::

            >>> print(session)

        And You will get all databases You worked with listed as (index, url)
        pairs. To connect to one of thouse databases
        just call session[index|url] and required
        Client object will be returned.

        :param data_file: path to session file
        :type data_file: string
    """

    def __init__(self, data_file='~/.openerp_proxy.json'):
        """
        """
        self.data_file = os.path.expanduser(data_file)

        # key: url; value: instance of DB or dict with init args
        self._databases = {}
        self._db_aliases = {}  # key: aliase name; value: url
        self._options = {}

        self._db_index = {}  # key: index; value: url
        self._db_index_rev = {}  # key: url; value: index
        self._db_index_counter = 0  # max index used

        if os.path.exists(self.data_file):
            data = json_read(self.data_file)

            self._databases = data.get('databases', {})
            self._db_aliases = data.get('aliases', {})
            self._options = data.get('options', {})

            if 'index' in data:
                for url, index in data['index'].items():
                    if url in self._databases:
                        self._db_index[index] = url
                        self._db_index_rev[url] = index
                        self._db_index_counter = max(self._db_index_counter,
                                                     index)

            for path in self.extra_paths:
                self.add_path(path)

            for module in self.start_up_imports:  # pragma: no cover
                try:
                    __import__(module)
                except ImportError:
                    # TODO: implement some logging
                    pass

    @property
    def extra_paths(self):
        """ List of extra pyhton paths, used by this session
        """
        return self.option('extra_paths', default=[])

    @property
    def start_up_imports(self):
        """ List of start-up imports

            If You want some module to be automaticaly imported on
            when session starts, that just add it to this list::

                session.start_up_imports.append('openerp_proxy.ext.sugar')
        """
        return self.option('start_up_imports', default=[])

    def add_path(self, path):
        """ Adds extra path to python import path.

            :param path: Paths to be added
            :type path: string
            :return: None

            Note: this way path will be saved in session
        """
        # TODO: rewrite extrapaths logic with custom importers. It will be more
        # pythonic
        if path not in sys.path:
            sys.path.append(path)
        if path not in self.extra_paths:
            self.extra_paths.append(path)

    def option(self, opt, val=None, default=None):
        """ Get or set option.
            if *val* is passed, *val* will be set as value for option,
            else just option value will be returned

            :param str opt: option to get or set value for
            :param val: value to be set for option *opt*
            :return: value of option *opt*

            Currently available options:

                - store_passwords (bool)   If set to True then all used
                  passwords will be stored on session.save. But be careful,
                  because of encription used for stored passwords is very week.

        """
        if val is not None:
            self._options[opt] = val
        elif opt not in self._options and default is not None:
            self._options[opt] = default
        return self._options.get(opt, default)

    @property
    def aliases(self):
        """ List of database aliases

            To add new database aliase, use method *aliase*::

                session.aliase('mdb', db)  # db is instance of Client
        """
        return self._db_aliases.copy()

    def aliase(self, name, val):
        """ Sets up aliase 'name' for *val*

            :param name: new aliase
            :type name: string
            :param val: database to create aliase for
            :type val: int|string|Client instance

            *val* could be index, url or Client object::

                session.aliase('tdb', 1)
                session.aliase('mdb', 'xml-rpc://me@my.example.com:8069/my_db')
                session.aliase('xdb', db)

            And now You can use this aliase like::

                session.tdb
                session.mdb
                session.xdb

            :return: unchanged val
        """
        if isinstance(val, Client):
            url = val.get_url()
        elif isinstance(val, numbers.Integral) and val in self.index:
            url = self.index[val]
        else:
            url = val

        if url in self._databases:
            self._db_aliases[name] = url
        else:
            raise ValueError("Bad value type: %s" % val)

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
    def index_rev(self):
        """ Reverse index.

            Property which returns dict with {url: index}
        """
        if not self._db_index_rev:
            for url in self._databases.keys():
                self._index_url(url)
        return dict(self._db_index_rev)

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

    def add_db(self, db):
        """ Add db to session.

            param db: database (client instance) to be added to session
            type db: Client instance
        """
        url = db.get_url()
        self._databases[url] = db
        self._index_url(url)

    def get_db(self, url_or_index, **kwargs):
        """ Returns instance of Client object, that represents single
            Odoo database it connected to, specified by passed index (integer)
            or url (string) of database, previously saved in session.

            :param url_or_index: must be integer (if index) or string (if url).
                                 this parametr specifies database
                                 to get from session
            :type url_or_index: int|string
            :param kwargs: can contain aditional arguments
                           to be passed on init of Client
            :return: Client instance
            :raises ValueError: if cannot find database by specified args

            Examples::

                session.get_db(1)   # using index
                session.get_db('xml-rpc://katyukha@erp.jbm.int:8069/jbm0')
                session.get_db('my_db')   # using aliase
        """
        if isinstance(url_or_index, numbers.Integral):
            url = self.index[url_or_index]
        else:
            url = self._db_aliases.get(url_or_index, url_or_index)

        db = self._databases.get(url, False)
        if not db:
            raise ValueError("Bad url %s. not found in history or databases"
                             "" % url)

        if isinstance(db, Client):
            return db

        ep_args = db.copy()  # DB here is instance of dict
        ep_args.update(**kwargs)

        if 'pwd' not in ep_args:
            if self.option('store_passwords') and 'password' in ep_args:
                import base64
                encoded_pwd = ep_args.pop('password').encode('utf8')
                crypter, password = base64.b64decode(encoded_pwd).split(b':')
                if crypter == b'simplecrypt':  # pragma: no cover
                    import simplecrypt
                    ep_args['pwd'] = simplecrypt.decrypt(
                        Client.to_url(ep_args), base64.b64decode(password))
                elif crypter == b'plain':
                    ep_args['pwd'] = password.decode('utf-8')
                else:  # pragma: no cover
                    raise Exception("Unknown crypter (%s) used in session"
                                    "" % repr(crypter))
            else:
                ep_args['pwd'] = getpass('Password: ')  # pragma: no cover

        db = Client(**ep_args)
        self.add_db(db)
        return db

    @property
    def db_list(self):
        """ Returns list of URLs of databases available in current session

            :return: list of urls of databases from session
            :rtype: list of strings
        """
        return self._databases.keys()

    def connect(self, host=None, dbname=None, user=None, pwd=None, port=8069,
                protocol='xml-rpc', interactive=True, no_save=False):
        """ Wraper around Client constructor class
            to simplify connect from shell.

            :param str host: host name to connect to
                             (will be asked interactvely if not provided)
            :param str dbname: name of database to connect to
                               (will be asked interactvely if not provided)
            :param str user: user name to connect as
                             (will be asked interactvely if not provided)
            :param str pwd: password for selected user
                            (will be asked interactvely if not provided)
            :param int port: port to connect to. (default: 8069)
            :param bool interactive: ask for connection parameters
                                     if not provided. (default: True)
            :param bool no_save: if set to True database
                                 will not be saved to session
            :return: Client object
        """
        if interactive:  # pragma: no cover
            # ask user for connection data if not provided, if interactive set
            # to True
            host = host or xinput('Server Host: ')
            dbname = dbname or xinput('Database name: ')
            user = user or xinput('Login: ')
            pwd = pwd or getpass("Password: ")

        url = Client.to_url(inst=None,
                            user=user,
                            host=host,
                            dbname=dbname,
                            port=port,
                            protocol=protocol)

        db = self._databases.get(url, False)
        if isinstance(db, Client):
            return db

        db = Client(host=host,
                    dbname=dbname,
                    user=user,
                    pwd=pwd,
                    port=port,
                    protocol=protocol)
        self.add_db(db)

        # if set to True, disalows saving database connection in session
        db._no_save = no_save
        return db

    def _get_db_init_args(self, database):
        if isinstance(database, Client):
            res = database.get_init_args()
            if self.option('store_passwords') and database._pwd:
                import base64
                password = base64.b64encode(
                    b'plain:' + database._pwd.encode('utf-8')).decode('utf-8')
                res.update({'password': password})
            return res
        elif isinstance(database, dict):
            return database
        else:  # pragma: no cover
            raise ValueError("Bad database instance. "
                             "It should be dict or Client object")

    def save(self):
        """ Saves session on disc
        """
        databases = {}
        for url, database in self._databases.items():
            if not getattr(database, '_no_save', False):
                init_args = self._get_db_init_args(database)
                databases[url] = init_args

        data = {
            'databases': databases,
            'aliases': self._db_aliases,
            'options': self._options,
            'index': self.index_rev,
        }

        json_write(self.data_file, data, indent=4)

    # Overridden to be able to access database like
    # session[url_or_index]
    def __getitem__(self, url_or_index):
        try:
            res = self.get_db(url_or_index)
        except ValueError as e:
            raise KeyError(str(e))
        return res

    # Overriden to be able to access database like
    # session.my_db
    def __getattr__(self, name):
        try:
            res = self.get_db(name)
        except ValueError as e:
            raise AttributeError(str(e))
        return res

    def __str__(self):
        return pprint.pformat(self.index)

    def __dir__(self):
        res = super(Session, self).__dir__()
        res += self.aliases.keys()
        return res

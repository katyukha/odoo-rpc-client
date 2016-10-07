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
        self._no_save = kwargs.pop('no_save', False)
        super(SessionClientExt, self).__init__(*args, **kwargs)

    def get_init_args(self):
        res = super(SessionClientExt, self).get_init_args()
        res.update({'no_save': self._no_save})
        return res


class ClientManager(object):
    """ Manage Client instances
    """
    def __init__(self, data=None):
        # key: url; value: instance of DB or dict with init args
        self._clients = {}
        self._aliases = {}  # key: aliase name; value: url

        self._cl_index = {}  # key: index; value: url
        self._cl_index_rev = {}  # key: url; value: index
        self._cl_index_counter = 0  # max index used

        if data is not None:
            self._parse_data(data)

    def _parse_data(self, data):
        """ Parse initial data

            Data should be a dictionary with following keys:

            - client
            - aliases
            - index
        """
        self._clients = data.get('clients', {})
        self._aliases = data.get('aliases', {})

        index = data.get('index', {})
        for url, index in index.items():
            if url in self._clients:
                self._cl_index[index] = url
                self._cl_index_rev[url] = index
                self._cl_index_counter = max(self._cl_index_counter,
                                             index)

    def _get_data(self):
        """ Return client manager's data, suitable (for example)
            to be written to json file

            :rtype: dict
        """
        clients = {}
        for url, client in self._clients.items():
            params = self._get_client_params(client)
            if not params.pop('no_save', False):
                clients[url] = params

        return {
            'clients': clients,
            'aliases': self.aliases,
            'index': self.index_rev,
        }

    @property
    def data(self):
        """ Return client manager's data, suitable (for example)
            to be written to json file

            :rtype: dict
        """
        return self._get_data()

    def _get_client_params(self, client):
        """ Returns dictionary with params that could be used to
            initialize new Client instance.

            :param client: Client to get params for
            :type client: openerp_proxy.core.Client
            :return: dict with client params
            :rtype: dict
        """
        if isinstance(client, Client):
            return client.get_init_args()
        elif isinstance(client, dict):
            return client
        else:  # pragma: no cover
            raise ValueError("Bad database instance. "
                             "It should be dict or Client object")

    @property
    def aliases(self):
        """ List of client aliases

            To add new client aliase, use method *aliase*::

                session = ClientManager()
                session.aliase('mdb', db)  # db is instance of Client
        """
        return self._aliases

    def aliase(self, name, val):
        """ Sets up aliase 'name' for *val*

            :param name: new aliase
            :type name: string
            :param val: client to create aliase for
            :type val: int|string|Client instance

            *val* could be index, url or Client object::

                session = ClientManager()
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

        if url in self._clients:
            self._aliases[name] = url
        else:
            raise ValueError("Bad value type: %s" % val)

        return val

    @property
    def index(self):
        """ Property which returns dict with {index: url}
        """
        if not self._cl_index:
            for url in self._clients.keys():
                self._index_url(url)
        return dict(self._cl_index)

    @property
    def index_rev(self):
        """ Reverse index.

            Property which returns dict with {url: index}
        """
        if not self._cl_index_rev:
            for url in self._clients.keys():
                self._index_url(url)
        return dict(self._cl_index_rev)

    def _index_url(self, url):
        """ Returns index of specified URL, or adds it to
            store assigning new index
        """
        if self._cl_index_rev.get(url, False):
            return self._cl_index_rev[url]

        self._cl_index_counter += 1
        self._cl_index[self._cl_index_counter] = url
        self._cl_index_rev[url] = self._cl_index_counter
        return self._cl_index_counter

    def add_client(self, client):
        """ Add db to session.

            :param client: client instance to be added to session
            :type client: openerp_proxy.core.Client
        """
        url = client.get_url()
        self._clients[url] = client
        self._index_url(url)

    def del_client(self, client):
        """ Remove db from session.

            :param client: client instance to be removed from session
            :type client: openerp_proxy.core.Client
        """
        url = client.get_url()
        index = self.index_rev[url]

        del self._cl_index_rev[url]
        del self._cl_index[index]
        del self._clients[url]

        for aliase, a_url in dict(self._aliases).items():
            if a_url == url:
                del self._aliases[aliase]

    def _create_client(self, data):
        """ Creates client from data

            :param dict data: dictionary with client params
            :return: Client instance
            :rtype: openerp_proxy.client
        """
        return Client(**data)

    def get_client(self, url_or_index):
        """ Returns instance of Client object, that represents single
            Odoo database it connected to, specified by passed index (integer)
            or url (string) of database, previously saved in manager.

            :param url_or_index: must be integer (if index) or string (if url).
                                 this parametr specifies client to get
            :type url_or_index: int|string
            :return: openerp_proxy.Client
            :raises ValueError: if cannot find client by specified args

            Examples::

                session.get_db(1)   # using index
                session.get_db('xml-rpc://admin@localhost:8069/test-odoo-db')
                session.get_db('my_db')   # using aliase
        """
        if isinstance(url_or_index, numbers.Integral):
            url = self.index[url_or_index]
        else:
            url = self._aliases.get(url_or_index, url_or_index)

        cl = self._clients.get(url, False)

        if not cl:
            cl = Client.from_url(url)
            self.add_client(cl)

        if isinstance(cl, Client):
            return cl

        cl = self._create_client(cl)
        self.add_client(cl)
        return cl

    @property
    def list(self):
        """ Returns list of URLs of clients registered in this manager

            :return: list of urls of clients registered in this manager
            :rtype: list of strings
        """
        return self._clients.keys()

    def __contains__(self, name):
        """ Test if database url is in this manager
        """
        return name in self._clients


class SessionClientManager(ClientManager):
    """ Client manager for sessions
    """

    def __init__(self, session, data):
        super(SessionClientManager, self).__init__(data)
        self.session = session

    def _create_client(self, data):
        """ Creates client from data

            implements some password obfuscation

            :param dict data: dictionary with client params
            :return: Client instance
            :rtype: openerp_proxy.client
        """
        if 'pwd' not in data:
            data = data.copy()
            if self.session.option('store_passwords') and 'password' in data:
                import base64
                encoded_pwd = data.pop('password').encode('utf8')
                crypter, password = base64.b64decode(encoded_pwd).split(b':')
                if crypter == b'simplecrypt':  # pragma: no cover
                    # Legacy support
                    import simplecrypt
                    data['pwd'] = simplecrypt.decrypt(
                        Client.to_url(data), base64.b64decode(password))
                elif crypter == b'plain':
                    # Current crypter
                    data['pwd'] = password.decode('utf-8')
                else:  # pragma: no cover
                    raise Exception("Unknown crypter (%s) used in session"
                                    "" % repr(crypter))
            else:
                # TODO: check if in interactive mode
                data['pwd'] = getpass('Password: ')  # pragma: no cover

        return super(SessionClientManager, self)._create_client(data)

    def _get_client_params(self, client):
        """ Returns dictionary with params that could be used to
            initialize new Client instance.

            implements some password deobfuscation

            :param client: Client to get params for
            :type client: openerp_proxy.core.Client
            :return: dict with client params
            :rtype: dict
        """
        params = super(SessionClientManager, self)._get_client_params(client)
        if (isinstance(client, Client) and
                self.session.option('store_passwords') and
                client._pwd):
            import base64
            password = base64.b64encode(
                b'plain:' + client._pwd.encode('utf-8')).decode('utf-8')
            params.update({'password': password})
        return params


class SessionClientManagerCompat(SessionClientManager):
    """ Client manager for sessions

        Used for backward compatability with old session formats
    """

    def _parse_data(self, data):
        """ Parse initial data

            If there is old 'databases' section in data,
            replace it with new 'clients' section
        """
        if 'clients' not in data and 'databases' in data:
            # Backward compatability
            data = data.copy()
            data['clients'] = data.pop('databases', {})
        return super(SessionClientManagerCompat, self)._parse_data(data)

    def _get_data(self):
        """ Modify data to be suitable for old format
            :rtype: dict
        """
        res = super(SessionClientManagerCompat, self)._get_data()
        res['databases'] = res.pop('clients', {})
        return res


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

        self._options = {}
        data = None
        if os.path.exists(self.data_file):
            data = json_read(self.data_file)
            self._options = data.get('options', {})

            for path in self.extra_paths:
                self.add_path(path)

            for module in self.start_up_imports:  # pragma: no cover
                try:
                    __import__(module)
                except ImportError:
                    # TODO: implement some logging
                    pass

        self._clients = SessionClientManagerCompat(self, data)

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

    # --- ClientManager proxy methods ---
    @property
    def aliases(self):
        """ List of database aliases

            To add new database aliase, use method *aliase*::

                session.aliase('mdb', db)  # db is instance of Client
        """
        return self._clients.aliases

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
        return self._clients.aliase(name, val)

    @property
    def index(self):
        """ Property which returns dict with {index: url}
        """
        return self._clients.index

    @property
    def index_rev(self):
        """ Reverse index.

            Property which returns dict with {url: index}
        """
        return self._clients.index_rev

    @property
    def db_list(self):
        """ Returns list of URLs of databases available in current session

            :return: list of urls of databases from session
            :rtype: list of strings
        """
        return self._clients.list

    def add_db(self, db):
        """ Add db to session.

            :param db: database (client instance) to be added to session
            :type db: openerp_proxy.core.Client
        """
        self._clients.add_client(db)

    def del_db(self, db):
        """ Remove database from session

            :param db: database (client instance) to be removed from session
            :type db: openerp_proxy.core.Client
        """
        self._clients.del_client(db)

    def get_db(self, url_or_index):
        """ Returns instance of Client object, that represents single
            Odoo database it connected to, specified by passed index (integer)
            or url (string) of database, previously saved in session.

            :param url_or_index: must be integer (if index) or string (if url).
                                 this parametr specifies database
                                 to get from session
            :type url_or_index: int|string
            :return: Client instance
            :raises ValueError: if cannot find database by specified args

            Examples::

                session.get_db(1)   # using index
                session.get_db('xml-rpc://katyukha@erp.jbm.int:8069/jbm0')
                session.get_db('my_db')   # using aliase
        """
        return self._clients.get_client(url_or_index)
    # --- End ClientManager proxy methods ---

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

        if url in self.index_rev:
            return self.get_db(url)

        db = Client(host=host,
                    dbname=dbname,
                    user=user,
                    pwd=pwd,
                    port=port,
                    protocol=protocol,
                    no_save=no_save)
        self.add_db(db)
        return db

    def save(self):
        """ Saves session on disk
        """
        data = {
            'options': self._options,
        }
        data.update(self._clients.data)

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

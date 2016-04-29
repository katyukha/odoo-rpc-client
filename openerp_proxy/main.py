#!/usr/bin/env python
# -*- coding: utf8 -*-

import operator

HELP_HEADER = """
    Usage:
        >>> db = session.connect()
        >>> so_obj = db['sale.orderl']  # get object
        >>> dir(so_obj)  # Thid will show all default methods of object
        >>> so_id = 123 # ID of sale order
        >>> so_obj.read(so_id)
        >>> so_obj.write([so_id], {'note': 'Test'})
        >>> sm_obj = db['stock.move']
        >>>
        >>> # check availability of stock move (call server-side method)
        >>> sm_obj.check_assign([move_id1, move_id2,...])

    Available objects in context:
        Client  - class that represents single Odoo / OpenERP database and
                  provides methods to work with data. Session.connect method
                  usualy returns instances of this class.
        session - represents session of client, stores in home directory list
                  of databases user works with, to simplify work. It is simpler
                  to get list of databases you have worked with previously
                  when program starts, and to connect to them
                  without remembrering hosts, users, ports
                  and other unneccesary information
        getpass - getpass.getpass functon from standard python library.
                  useful, if you do not want live passwords in ipython history.

    Databases You previously worked with: %(databases)s

    Aliases: %(aliases)s

    Use index or url or aliase for session:
        session[1] or session[url] or session[aliase])
"""


def generate_header_databases(session):
    """ Prepare to display history of database connections
    """
    header_databases = "\n"
    for index, url in sorted(session.index.items(),
                             key=operator.itemgetter(0)):
        header_databases += "        - [%3s] %s\n" % (index, url)
    return header_databases


def generate_header_aliases(session):
    """ Prepare to display list of database aliases available
    """
    header_aliases = "\n"
    if session.aliases:
        max_aliase_len = max((len(i) for i in session.aliases))
        aliase_tmpl = "%%%ds" % max_aliase_len
        for aliase, url in session.aliases.items():
            header_aliases += "        - %s: %s\n" % (aliase_tmpl % aliase,
                                                      url)
    return header_aliases


def main():
    """ Entry point for running as standalone APP
    """
    from .session import Session
    from .core import Client
    from getpass import getpass

    session = Session()

    # generate header
    header_databases = generate_header_databases(session)
    header_aliases = generate_header_aliases(session)
    header = HELP_HEADER % {'databases': header_databases,
                            'aliases': header_aliases}

    _locals = {
        'Client': Client,
        'session': session,
        'getpass': getpass
    }
    try:
        from IPython import embed
        try:
            from IPython.terminal.ipapp import load_default_config
            ip_config = load_default_config()
        except:
            ip_config = None

        embed(user_ns=_locals, header=header, config=ip_config)
    except ImportError:
        from code import interact
        interact(local=_locals, banner=header)

    session.save()

if __name__ == '__main__':
    main()

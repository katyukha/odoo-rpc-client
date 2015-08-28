#!/usr/bin/env python
# -*- coding: utf8 -*-


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
        Client - class that represents single Odoo / OpenERP database and
                 provides methods to work with data. Session.connect method usualy
                 returns instances of this class.
        session - represents session of client, stores in home directory list
                  of databases user works with, to simplify work. It is simpler
                  to get list of databases you have worked with previously on program
                  start, and to connect to them without remembrering hosts, users, ports
                  and other unneccesary information

    Databases You previously worked with: %(databases)s

    Aliases: %(aliases)s

        (Use index or url or aliase for session: session[1] or session[url] or session[aliase])
"""


def main():
    """ Entry point for running as standalone APP
    """
    from .session import Session
    from .core import Client

    session = Session()

    header_databases = "\n"
    for index, url in session.index.items():
        header_databases += "        - [%3s] %s\n" % (index, url)

    header_aliases = "\n"
    for aliase, url in session.aliases.items():
        header_aliases += "        - %7s: %s\n" % (aliase, url)

    header = HELP_HEADER % {'databases': header_databases, 'aliases': header_aliases}

    _locals = {
        'Client': Client,
        'session': session,
    }
    try:
        from IPython import embed
        embed(user_ns=_locals, header=header)
    except ImportError:
        from code import interact
        interact(local=_locals, banner=header)

    session.save()

if __name__ == '__main__':
    main()


#!/usr/bin/env python
# -*- coding: utf8 -*-

from session import ERP_Session
from core import ERP_Proxy


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
        >>> # check availability of stock move
        >>> sm_obj.check_assign([move_id1, move_id2,...])

    Available objects in context:
        ERP_Proxy - class that represents single OpenERP database and
                    provides methods to work with data. Instances of this
                    class returned by connect() method of session object.
        session - represents session of client, stores in home directory list
                  of databases user works with, to simplify work. It is simpler
                  to get list of databases you have worked with previously on program
                  start, and to connect to them without remembrering hosts, users, ports
                  and other unneccesary information

    Databases You previously worked with: %(databases)s

        (Used index or url for session: session[1] or session[url])
"""


def main():
    """ Entry point for running as standalone APP
    """
    session = ERP_Session()

    header_databases = "\n"
    for index, url in session.index.iteritems():
        header_databases += "        - [%s] %s\n" % (index, url)

    header = HELP_HEADER % {'databases': header_databases}

    _locals = {
        'ERP_Proxy': ERP_Proxy,
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

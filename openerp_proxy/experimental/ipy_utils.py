"""This module contains some IPython integration utils
"""


def in_progress(seq, msg="Progress: [%(processed)d / %(total)d]", length=None):
    """ Iterate over sequence, yielding item with progress widget displayed.
        This is useful if you need to precess sequence of items with some
        time consuming operations

        .. note::

            This works only in Jupyter Notebook

        .. note::

            This function requires *ipywidgets* package to be installed

        :param seq: sequence to iterate on.
        :param str msg: (optional) message template to display.
                        available to use 'processed' and 'total' integer vars,
                        where 'processed' is number of items processed and
                        'total' is total number of items in seq.
        :param int length: (optional) if seq is generator, or it is not
                           possible to apply 'len(seq)' function to 'seq',
                           then this argument is required and it's value will
                           be used as total number of items in seq.

        Example example::

            import time
            for i in in_progress(range(10)):
                time.sleep(1)
    """
    from IPython.display import display
    from ipywidgets import IntProgress

    if length is None:
        length = len(seq)

    progress = IntProgress(value=0, min=0, max=length,
                           description=msg % {'processed': 0,
                                              'total': length})
    display(progress)

    for i, item in enumerate(seq, 1):
        progress.value = i
        progress.description = msg % {'processed': i, 'total': length}
        yield item

    progress.close()

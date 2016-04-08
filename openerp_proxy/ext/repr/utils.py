import os
import os.path
import collections


from ...utils import ustr as _
from ...utils import makedirs


# TODO: use enviroment var or some sort of config
# TODO: move this code somewhere from here
# Here we use paths based on current directory, because default IPython
# notebook configuration does not allow to access files located somewere else
GEN_FILE_PATH = os.path.normpath(os.path.join('.', 'tmp'))
CSV_PATH = os.path.join(GEN_FILE_PATH, 'csv')
REPORTS_PATH = os.path.join(GEN_FILE_PATH, 'reports')


# Create required paths
makedirs(CSV_PATH)
makedirs(REPORTS_PATH)


# HTML Templates
TMPL_INFO_WITH_HELP = u"""
<div class="container-fluid">
    <div class="row">
        <div class="panel panel-default col-md-7 col-lg-7">
            <div class="panel-heading">%(caption)s</div>
            <div class="panel-body">%(info)s</div>
        </div>
        <div class="panel panel-default col-md-5 col-lg-5">
            <div class="panel-heading">Info</div>
            <div class="panel-body">%(help)s</div>
        </div>
    </div>
</div>
"""

TMPL_TABLE = u"""
<table class="table table-bordered table-condensed %(extra_classes)s" style="margin-left:0;%(styles)s">
%(rows)s
</table>
"""

TMPL_TABLE_ROW = u"<tr>%s</tr>"
TMPL_TABLE_DATA = u"<td>%s</td>"
TMPL_TABLE_HEADER = u"<th>%s</th>"


def th(val):
    return TMPL_TABLE_HEADER % _(val)


def td(val):
    return TMPL_TABLE_DATA % _(val)


def tr(*args):
    return TMPL_TABLE_ROW % u"".join(args)


def describe_object_html(data, caption='', help='', table_styles='',
                         headers=None):
    """ Converts dictionary data to html table string

        :param dict|list data: dictionary like object.
                               must contain .items() method
                               represents object info to be displayed in table
                               or iterable table like structure, where
                               first element ofeach row is assumend
                               to be header
        :param str caption: table's caption
        :param str help: help message to be displayed near table
        :param str table_styles: string with styles for table
    """
    if isinstance(data, dict):
        html_data = u"".join((tr(th(k), td(v)) for k, v in data.items()))
    elif isinstance(data, collections.Iterable):
        html_data = u"".join((tr(th(line[0]), *[td(x) for x in line[1:]])
                              for line in data))

    if headers is not None:
        html_data = tr(*[th(x) for x in headers]) + html_data

    table = TMPL_TABLE % {'styles': table_styles,
                          'rows': html_data,
                          'extra_classes': ''}
    return TMPL_INFO_WITH_HELP % {'info': table, 'help': help, 'caption': caption}



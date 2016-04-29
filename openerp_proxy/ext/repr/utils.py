import os
import os.path

from jinja2 import Template

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
TMPL_OBJECT_DESCRIPTION = Template("""
<div class="container-fluid">
    <div class="row">
        <div class="panel panel-default col-md-7 col-lg-7">
            <div class="panel-heading">{{ caption }}</div>
            <div class="panel-body">
                <table class="table table-bordered table-condensed {{ extra_classes }}"
                       style="margin-left:0; {{ styles }}">
                    {% if headers %}
                        <tr>
                            {% for header in headers %}
                                <th>{{ header }}</th>
                            {% endfor %}
                        </tr>
                    {% endif %}
                    {% for row in data %}
                    <tr>
                        <th>{{ row[0] }}</th>
                        {% for cell in row[1:] %}
                            <td>{{ cell }}</td>
                        {% endfor %}
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>
        <div class="panel panel-default col-md-5 col-lg-5">
            <div class="panel-heading">Info</div>
            <div class="panel-body">{{ help }}</div>
        </div>
    </div>
</div>
""")  # noqa


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
        data = [(k, v) for k, v in data.items()]

    return TMPL_OBJECT_DESCRIPTION.render(data=data,
                                          styles=table_styles,
                                          extra_classes='',
                                          help=help,
                                          caption=caption,
                                          headers=headers)

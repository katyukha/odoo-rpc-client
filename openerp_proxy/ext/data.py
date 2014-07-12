from openerp_proxy.orm.record import ObjectRecords
from openerp_proxy.orm.record import RecordListBase
from openerp_proxy.orm.record import get_record_list_class
import collections
import functools


__all__ = ('ObjectData', 'RecordListData')


class RecordListData(RecordListBase):
    """ Extend record list to add aditional method to work with lists of records
    """

    def group_by(self, field_name):
        """ Groups all records in list by specifed field.

            for example we have list of sale orders and want to group it by state:

                # so_list - variable that contains list of sale orders selected
                # by some criterias. so to group it by state we will do:
                group = so_list.group_by('state')
                for state, rlist in group.iteritems():  # Iterate over resulting dictionary
                    print state, rlist.length    # Print state and amount of items with such state
        """
        cls_init = functools.partial(get_record_list_class(),
                                     self.object,
                                     fields=self._fields,
                                     context=self._context)
        res = collections.defaultdict(cls_init)
        for record in self.records:
            res[record[field_name]].append(record)
        return res


# TODO: implement some class wrapper to by default load only count of domains,
#       and by some method load ids, or records if required. this will allow to
#       work better with data when accessing root object showing all groups and
#       amounts of objects within, but when accessing some object we could get
#       records related to that group to analyse them.
class ObjectData(ObjectRecords):
    """ Provides aditional methods to work with data
    """

    def data__get_grouped(self, group_rules, count=True, records=False):
        """ Returns dictionary with grouped data. if count=True returns only amount of items found for rule
            otherwise returns list of ids found for each rule

            @param group_rules: dictionary with keys = group_names and values are domains or other dictionary
                                with domains.
                                For example:
                                    group_rules = {'g1': [('state','=','done')],
                                                   'g2': {
                                                        '__sub_domain': [('partner_id','=',5)],
                                                        'total': [],
                                                        'done': [('state', '=', 'done')],
                                                        'cancel': [('state', '=', 'cancel')]
                                                    }}
                                Each group may contain '__sub_domain' field with domain applied to all
                                items of group
            @param count: if True then in result dictinary only couns will be
                        other wie each group in result dictionary will contain list of IDs
                        of records found
            @param records: if True then all results will be wrapped into records
                            Other wise just IDs will be used
            @return: dictionary like 'group_rules' but with domains replaced by search result
        """
        result = {}
        sub_domain = group_rules.pop('__sub_domain', [])
        for key, value in group_rules.iteritems():
            if isinstance(value, (list, tuple)):  # If value is domain
                domain = sub_domain + value
                if records:
                    result[key] = self.search_records(domain, count=count)
                else:
                    result[key] = self.search(domain, count=count)
            elif isinstance(value, dict):  # if value is subgroup of domains
                _sub_domain = sub_domain + value.get('__sub_domain', [])
                if _sub_domain:
                    value['__sub_domain'] = _sub_domain
                result[key] = self.data__get_grouped(value, count=count, records=records)
            else:
                raise TypeError("Unsupported type for 'group_rules' value for key %s: %s" % (key, type(value)))
        return result


""" This module provides extension which allows aditional
data manipulations, especialy filtering and grouping capabilities.
"""
from openerp_proxy.orm.record import ObjectRecords
from openerp_proxy.orm.record import RecordList, get_record_list
import collections
import functools


__all__ = ('ObjectData', 'RecordListData')


class RecordListData(RecordList):
    """ Extend record list to add aditional method to work with lists of records
    """

    def group_by(self, grouper):
        """ Groups all records in list by specifed grouper.

            :param grouper: field name or callable to group results by.
                            if function is passed, it should receive only
                            one argument - record instance, and result of
                            calling grouper will be used to group records.
            :type grouper: string|callable(record)

            for example we have list of sale orders and want to group it by state::

                # so_list - variable that contains list of sale orders selected
                # by some criterias. so to group it by state we will do:
                group = so_list.group_by('state')
                for state, rlist in group.iteritems():  # Iterate over resulting dictionary
                    print state, rlist.length           # Print state and amount of items with such state

            or imagine that we would like to groupe records by last letter of sale order number::

                # so_list - variable that contains list of sale orders selected
                # by some criterias. so to group it by last letter of sale
                # order name  we will do:
                group = so_list.group_by(lambda so: so.name[-1])
                for letter, rlist in group.iteritems():  # Iterate over resulting dictionary
                    print letter, rlist.length           # Print state and amount of items with such state
        """
        cls_init = functools.partial(get_record_list,
                                     self.object,
                                     ids=[],
                                     cache=self._cache)
        res = collections.defaultdict(cls_init)
        for record in self.records:
            if isinstance(grouper, basestring):
                key = record[grouper]
            elif callable(grouper):
                key = grouper(record)

            res[key].append(record)
        return res

    def filter(self, func):
        """ Filters items using *func*.

            :param func: callable to check if record should be included in result.
                         also *openerp_proxy.utils.r_eval* may be used
            :type func: callable(record)->bool
            :return: RecordList which contains records that matches results
            :rtype: RecordList
        """
        result_ids = [record.id for record in self.records if func(record)]
        return get_record_list(self.object, ids=result_ids, cache=self._cache)


# TODO: implement some class wrapper to by default load only count of domains,
#       and by some method load ids, or records if required. this will allow to
#       work better with data when accessing root object showing all groups and
#       amounts of objects within, but when accessing some object we could get
#       records related to that group to analyse them.
class ObjectData(ObjectRecords):
    """ Provides aditional methods to work with data
    """

    def data__get_grouped(self, group_rules, count=False):
        """ Returns dictionary with grouped data. if count=True returns only amount of items found for rule
            otherwise returns list of records found for each rule

            :param group_rules: dictionary with keys=group_names and values are domains or other dictionary
                                with domains.
                                For example

                                ::

                                    group_rules = {'g1': [('state','=','done')],
                                                   'g2': {
                                                        '__sub_domain': [('partner_id','=',5)],
                                                        'total': [],
                                                        'done': [('state', '=', 'done')],
                                                        'cancel': [('state', '=', 'cancel')]
                                                    }}

                                Each group may contain '__sub_domain' field with domain applied to all
                                items of group
            :type group_rules: dict
            :param count: if True then result dictinary will contain only counts
                          otherwise each group in result dictionary will contain RecordList of records found
            :type count: boolean (default: False)
            :return: dictionary like 'group_rules' but with domains replaced by search result (RecordList instance).
        """
        result = {}
        sub_domain = group_rules.pop('__sub_domain', [])
        for key, value in group_rules.iteritems():
            if isinstance(value, (list, tuple)):  # If value is domain
                domain = sub_domain + value
                result[key] = self.search_records(domain, count=count)
            elif isinstance(value, dict):  # if value is subgroup of domains
                _sub_domain = sub_domain + value.get('__sub_domain', [])
                if _sub_domain:
                    value['__sub_domain'] = _sub_domain
                result[key] = self.data__get_grouped(value, count=count)
            else:
                raise TypeError("Unsupported type for 'group_rules' value for key %s: %s" % (key, type(value)))
        return result


from openerp_proxy.orm.record import ObjectRecords


__all__ = ('ObjectData')


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
                                                    'total': [],
                                                    'done': [('state', '=', 'done')],
                                                    'cancel': [('state', '=', 'cancel')]
                                                }}
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


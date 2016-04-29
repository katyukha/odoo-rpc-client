""" This extension module provides aditional logic
to ease work with workflows. For example it provides methods
to easily get workflow instance or workflow workitems related
to specific record, or to easily get workflow related to Object.
Also it provides simple methods to easily send workflow signals
to records from Object and Record interfaces.
"""
import numbers
import six


from ..orm.record import (Record,
                          ObjectRecords)
from ..exceptions import ObjectException


__all__ = ('RecordWorkflow', 'ObjectWorkflow')


class ObjectWorkflow(ObjectRecords):
    """ Modifies Object class, adding methods related to Workflow
    """
    def __init__(self, *args, **kwargs):
        super(ObjectWorkflow, self).__init__(*args, **kwargs)
        self._workflow = None

    @property
    def workflow(self):
        """ Returns Record instance of "workflow" object
            related to this Object

            If there are no workflow for an object then False will be returned
        """
        if self._workflow is None:
            wkf_obj = self.service.get_obj('workflow')
            # TODO: implement correct behavior for situations with few
            # workflows for same model.
            wkf_records = wkf_obj.search_records([('osv', '=', self.name)])
            if wkf_records and len(wkf_records) > 1:   # pragma: no cover
                raise ObjectException(
                    "More then one workflow per model not supported "
                    "be current version of openerp_proxy!")
            self._workflow = wkf_records and wkf_records[0] or False
        return self._workflow

    def workflow_signal(self, obj_id, signal):
        """ Triggers specified signal for object's workflow
        """
        assert isinstance(obj_id, numbers.Integral), "obj_id must be integer"
        assert isinstance(signal, six.string_types), "signal must be string"
        return self.client.execute_wkf(self.name, signal, obj_id)


class RecordWorkflow(Record):
    """ Adds ability to browse related fields from record
    """

    def __init__(self, *args, **kwargs):
        super(RecordWorkflow, self).__init__(*args, **kwargs)
        self._workflow_instance = None

    @property
    def workflow_instance(self):
        """ Retunrs workflow instance related to this record
        """
        if self._workflow_instance is None:
            wkf = self._object.workflow
            if not wkf:
                self._workflow_instance = False
            else:
                wkf_inst_obj = self._service.get_obj('workflow.instance')
                domain = [('wkf_id', '=', wkf.id),
                          ('res_id', '=', self.id)]
                wkf_inst_records = wkf_inst_obj.search_records(domain, limit=1)

                if wkf_inst_records:
                    self._workflow_instance = wkf_inst_records[0]
                else:
                    self._workflow_instance = False
        return self._workflow_instance

    @property
    def workflow_items(self):
        """ Returns list of related workflow.woritem objects
        """
        # TODO: think about adding caching
        workitem_obj = self._service.get_obj('workflow.workitem')
        wkf_inst = self.workflow_instance
        if wkf_inst:
            return workitem_obj.search_records([('inst_id', '=', wkf_inst.id)])
        return []

    def workflow_signal(self, signal):
        """ trigger's specified signal on record's related workflow
        """
        return self._object.workflow_signal(self.id, signal)

    def refresh(self):
        """Cleanup record caches and reread data
        """
        super(RecordWorkflow, self).refresh()
        self._workflow_instance = None
        return self

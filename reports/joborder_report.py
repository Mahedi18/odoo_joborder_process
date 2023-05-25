import time
from openerp.osv import osv
from openerp.report import report_sxw
from openerp.tools import amount_to_text
from datetime import datetime
from openerp.tools import amount_to_text
from openerp.tools import amount_to_text_en


class joborder_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        self.count = 1
        super(joborder_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_remaing': self.get_remaing,

        })

    def get_remaing(self, job_order_report):
        qty = 0.0
        for val in job_order_report:
            qty = val.total_issue - val.total_receive
        return qty


class joborder_report_first(osv.AbstractModel):
    _name = 'report.job_order_process.joborder_report_first'
    _inherit = 'report.abstract_report'
    _template = 'job_order_process.joborder_report_first'
    _wrapped_report_class = joborder_report
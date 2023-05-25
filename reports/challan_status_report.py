import time
from openerp.osv import osv
from openerp.report import report_sxw
from openerp.tools import amount_to_text
from datetime import datetime
from openerp.tools import amount_to_text
from openerp.tools import amount_to_text_en


class challan_status_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):

        self.count = 1
        super(challan_status_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
                                'get_challan_name':self.get_challan_name,
                                'get_name':self.get_name,
                                'get_heat': self.get_heat,
                                'get_date':self.get_date,
                                'get_issue':self.get_issue,
                                'get_receive':self.get_receive,
                                'get_remaining':self.get_remaining,
                                'get_total_remaing':self.get_total_remaing,


                                })

    def get_challan_name(self,job_order_report):
        tax_list = []
        tax_list1 = []
        for val in job_order_report.joborder_report_line:
            tax_list.append(val.challan_id.id)
        if tax_list:
            tax_list = list(set(tax_list))
            tax_list1 = sorted(tax_list)
        return tax_list1

    def get_name(self, tax_list1):
        str1 = ' '
        if tax_list1:
            obj = self.pool.get('joborder.challan').browse(self.cr, self.uid, tax_list1)
            str1 = ''.join(obj.name)
        return str1

    def get_heat(self, tax_list1):
        str6 = ' '
        if tax_list1:
            obj = self.pool.get('joborder.challan').browse(self.cr, self.uid, tax_list1)
            str6 = (obj.heat_no.name)
        return str6

    def get_date(self, tax_list1):
        str2 = ' '
        if tax_list1:
            obj = self.pool.get('joborder.challan').browse(self.cr, self.uid, tax_list1)
            str2 = ''.join(obj.date)
        return str2

    def get_issue(self, tax_list1):
        str3 = ' '
        if tax_list1:
            obj = self.pool.get('joborder.challan').browse(self.cr, self.uid, tax_list1)
            str3 = (obj.total_issue)
        return str3

    def get_receive(self, tax_list1):
        str4 = 0.0
        if tax_list1:
            obj = self.pool.get('joborder.challan').browse(self.cr, self.uid, tax_list1)
            str4 = (obj.total_receive)
        return str4

    def get_remaining(self, tax_list1):
        str5 = 0.0
        if tax_list1:
            obj = self.pool.get('joborder.challan').browse(self.cr, self.uid, tax_list1)
            str5 = (obj.total_issue - obj.total_receive)
        return str5

    def get_total_remaing(self, job_order_report):
        qty = 0.0
        for val in job_order_report:
            qty = val.total_issue - val.total_receive
        return qty

class challan_status_report_first(osv.AbstractModel):
    _name = 'report.job_order_process.challan_status_report_first'
    _inherit = 'report.abstract_report'
    _template = 'job_order_process.challan_status_report_first'
    _wrapped_report_class = challan_status_report
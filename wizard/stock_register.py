import time
from odoo import api, fields, models
from datetime import datetime,timedelta
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning



class StockRegisterTrna(models.TransientModel):
    _name = 'stock.register.tran'

    @api.multi
    def print_report(self):
        print('============stork reg report',self)
        if self.from_date and self.to_date:

            return self.env.ref('job_order_process.stock_register_report').report_action(self)
    def all_incomming(self,party):
        line_list = []
        line_list1 = []
        receive_obj = self.env['joborder.challan.receipt'].search([('date', '>=', self.from_date),('date', '<=', self.to_date),('partner_id', '=', party)])
        for val in receive_obj:
            if val.joborder_challan_receipt_lines:
                for val1 in val.joborder_challan_receipt_lines:
                    line_list.append(val1.id)
                    if line_list:
                        line_list = list(set(line_list))
                        line_list1 = sorted(line_list)
        return line_list1
    def get_party(self):
        party_list = []
        party_list1 = []
        receive_obj = self.env['joborder.challan.receipt'].search(
            [('date', '>=', self.from_date), ('date', '<=', self.to_date), ('partner_id', '<=', self.partner_id.id)])
        for val in receive_obj:
            if val.partner_id:
                for val1 in val.partner_id:
                    party_list.append(val1.id)
                    if party_list:
                        party_list = list(set(party_list))
                        party_list1 = sorted(party_list)
        return party_list1
    def get_name_party(self,party_list1):
        if party_list1:
            party_obj = self.env['my.partner'].browse(party_list1)
            a = party_obj.name
        return a
    def get_date(self,line_list1):
        if line_list1:
            line_obj = self.env['joborder.challan.receipt.line'].browse(line_list1)
            a = line_obj.order_id.date

        return a
    def get_challan(self,line_list1):
        if line_list1:
            line_obj = self.env['joborder.challan.receipt.line'].browse(line_list1)
            a = line_obj.order_id.name
        return a
    def get_issue(self,challan):
        challan_list=[]
        challan_list1=[]
        if challan:
            challan_obj = self.env['challan.line'].search([('party_challan.name', '=',challan)])

            for val in challan_obj:
                challan_list.append(val.order_id.id)
                if challan_list:
                    challan_list = list(set(challan_list))
                    challan_list1 = sorted(challan_list)
            return challan_list1
    def get_issue_challan_product(self,challan,product):
        if challan:
            issue_challan_obj = self.env['joborder.challan'].browse(challan)
            line_obj = self.env['challan.line'].search([('product_id.name', '=',product),('order_id', '=',issue_challan_obj.id)])
        return line_obj
    def get_issue_challan(self,v):
        if v:
            issue_challan_obj = self.env['joborder.challan'].browse(v)
            a = issue_challan_obj.name

        return a
    def get_issue_challan_date(self,v):
        if v:
            issue_challan_obj = self.env['joborder.challan'].browse(v)
            a = issue_challan_obj.date

        return a
    def get_party_name(self,line_list1):
        if line_list1:
            line_obj = self.env['joborder.challan.receipt.line'].browse(line_list1)
            a = line_obj.order_id.partner_id.name
        return a
    def get_part_name(self,line_list1):
        if line_list1:
            line_obj = self.env['joborder.challan.receipt.line'].browse(line_list1)
            a = line_obj.product_id.name
        return a
    def get_receive_qty(self,line_list1):
        if line_list1:
            line_obj = self.env['joborder.challan.receipt.line'].browse(line_list1)
            a = line_obj.qty
        return a
    def get_remaining_qty(self,line_list1):
        if line_list1:
            line_obj = self.env['joborder.challan.receipt.line'].browse(line_list1)
            a = line_obj.qty_remaining
        return a
    def get_issue_qty(self,v,name):
        a = 0
        if v:
            issue_challan_obj = self.env['joborder.challan'].browse(v)

            line_obj = self.env['challan.line'].search([('product_id.name', '=',name),('order_id', '=',issue_challan_obj.id)])
            for val in line_obj:


                a = a + val.qty
        return a
    def get_rem_qty(self,issue,rec):
        total_issue = 0.0
        if issue and rec:
            total_issue = total_issue + issue
            total_rem = rec - total_issue
        return total_rem


    from_date = fields.Date('From Date',default='2019-01-01')
    to_date = fields.Date('To Date',default=datetime.today())
    partner_id = fields.Many2one('my.partner','Partner')
    challan_type = fields.Selection([('regular', 'Regular'),('rework', 'Rework'),('foc', 'FOC')],default='regular',string='Challan Type')
    user_id = fields.Many2one('res.users', 'Created By', default=lambda self: self.env.user)



from odoo import api, fields, models,_
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class DispatchAdvice(models.Model):
    _name="dispatch.advice"
    _order = 'id desc'

    def get_time(self):
        date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        date_time = datetime.strptime(date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5, minutes=30, seconds=0)
        date_time  = date_time .strftime('%H:%M')
        return date_time

    def action_confirm(self):
        self.write({'state':'confirm'})

    name = fields.Char('Dispatch Advice No.', required=True,default='New')
    partner_id = fields.Many2one('my.partner','Party Name',required=True,)
    # date = fields.Date('Date',default=fields.Date.today(),required=True,)
    date = fields.Date(required=True, default=lambda self: self._get_current_date())

    @api.model
    def _get_current_date(self):
        """ :return current date """
        return fields.Date.today()
    remark = fields.Char('Remark')
    dispatch_advice_line = fields.One2many('dispatch.advice.line','order_id','Lines')
    user_id = fields.Many2one('res.users', 'Created By', default=lambda self: self.env.user)
    vehicle_no = fields.Many2one('vehicle', 'Vehicle No')
    time = fields.Char('Time',default=get_time)
    challan_type = fields.Selection([('regular', 'Regular'),('rework', 'Rework'),('foc', 'FOC'),('return','Return'),('osp','Returnable Challan')],default='regular',string='Challan Type',required=True)
    description = fields.Char('Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
    ], string='Status', readonly=True, copy=False, index=True, default='draft')
    payment_term_recs = fields.Integer(string="Payment term (days)")

    _sql_constraints = [
        ('name', 'unique(name,partner_id)', 'Dispatch no. already exists for this party!')
    ]

class DispatchAdviceLine(models.Model):
    _name = "dispatch.advice.line"

    @api.onchange('product_id')
    def onchange_product_id(self):
        qty = 0
        product_list = []
        for line in self.env['joborder.challan.receipt.line'].search(
                [('order_id.partner_id', '=', self.order_id.partner_id.id), ('order_id.challan_type', '=', self.order_id.challan_type),
                 ('bal_qtynew', '>', 0)]):
            product_list.append(line.product_id.id)
        product_list = list(set(product_list))
        domain = {'product_id': [('id', 'in', product_list)]}
        if self.product_id:
            for val in self.env['joborder.challan.receipt.line'].search(
                    [('product_id', '=', self.product_id.id), ('bal_qtynew', '>', 0),
                     ('order_id.partner_id', '=', self.order_id.partner_id.id),
                     ('order_id.challan_type', '=', self.order_id.challan_type)]):
                # print(val,'==============================val')
                qty+=val.bal_qtynew
            self.qty = qty
            self.part_no = self.product_id.part_no
            self.unit_id = self.product_id.unit_id.id
            self.qty_nos = qty if (self.product_id.unit_id.name.lower())[0] == 'n' else 0
            self.qty_kg = qty if (self.product_id.unit_id.name.lower())[0] != 'n' else 0
        return {'domain':domain}

    order_id = fields.Many2one('dispatch.advice','Id',ondelete='cascade')
    product_id = fields.Many2one('my.product','Product',required=True)
    name = fields.Char('Description',default='After Platting')
    part_no=fields.Char('Part No.')
    hsn_code = fields.Char('HSN No.')
    unit_id = fields.Many2one('my.unit', 'UOM',readonly=True)
    qty = fields.Float('Quantity',digits=(10,2))
    qty_nos=fields.Integer('Qty Nos')
    qty_kg=fields.Float('Qty_Kg',digits=(10,2))
    nature_of_process = fields.Char('Nature of Process')


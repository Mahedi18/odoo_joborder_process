from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class JobOrder(models.Model):
    _name="job.order"
    _order = 'mast_oldid desc'

    # @api.model
    # def create(self, vals):
    #     seq = self.env['ir.sequence'].get('job_order')
    #     vals['name'] = 'JOB' + str(seq)
    #     sum_id = super(JobOrder, self).create(vals)
    #     return sum_id






    @api.multi
    def unlink(self):
        if self.env.user.id == self.env.ref('base.user_admin').id:
            return super(JobOrder, self).unlink()
        else:
            raise ValidationError('You Can not delete a record')

    @api.multi
    def action_done(self):
        self.write({'state': 'done'})
        return True

    def action_confirm(self):
        self.write({'state':'confirm'})
        return True


    def _amount_all_wrapper(self):
        total_amount = 0.00
        for val in self:
            if val.joborder_line:
                for val1 in val.joborder_line:
                    total_amount = total_amount + val1.price_subtotal
                    self.amount_untaxed = total_amount

    def _tax_amount(self):
        total_tax = 0.00
        for val in self:
            if val.joborder_line:
                for val1 in val.joborder_line:
                    amount = 0.0
                    if val1.tax_id:
                        amount = amount + val1.tax_id.amt

                    total_tax = total_tax + (val1.qty * val1.unit_price) * amount / 100
                    self.tax_value = total_tax

    def _get_total_amount(self):
        total_amount = 0.00
        for val in self:
            total_amount = val.amount_untaxed + val.tax_value
            self.total_amount = total_amount


    name = fields.Char('job Order', required=True,)
    partner_id = fields.Many2one('my.partner','Party Name',required=True,)
    # date = fields.Date('Date',default=fields.Date.today(),required=True,)
    date = fields.Date(required=True, default=lambda self: self._get_current_date())
    @api.model
    def _get_current_date(self):
        """ :return current date """
        return fields.Date.today()

    remark = fields.Char('Remark')
    joborder_line = fields.One2many('job.order.line','order_id','Lines',required=True,)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('done', 'Close'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    amount_untaxed = fields.Float(compute=_amount_all_wrapper, string='Untaxed Amount')
    tax_value = fields.Float(compute=_tax_amount, string='Taxes')
    total_amount = fields.Float(compute=_get_total_amount, string='Total Amount')
    payment_term = fields.Integer('Payment Term(days)',default=30)
    mast_oldid=fields.Integer('Mast Id')
    challan_receipt_count = fields.Integer('Challan Receipt Count', compute="action_view_challan_receipt_count")
    challan_issue_count = fields.Integer('Challan Issue Count', compute="action_view_challan_issue_count")


    def action_view_challan_issue_count(self):
        for val in self:
            challan_issue_data = self.env['challan.line'].sudo().read_group(
                [('job_order_id', '=', val.id),('order_id.partner_id', '=', val.partner_id.id)], ['id'], ['job_order_id'])
            # print(challan_issue_data,'===================challan')
            result = dict((data['job_order_id'][0], data['job_order_id_count']) for data in challan_issue_data)
            val.challan_issue_count = result.get(self.id, 0)

    def open_challan_issue_history(self):
        action = self.env.ref('job_order_process.action_challan').read()[0]
        action['domain'] = [('partner_id', '=', self.partner_id.id),('challan_line.job_order_id', '=', self.id)]
        return action


    def action_view_challan_receipt_count(self):
        for val in self:
            challan_receive_data = self.env['joborder.challan.receipt.line'].sudo().read_group(
                [('job_order_id', '=', val.id),('order_id.partner_id', '=', val.partner_id.id)], ['id'], ['job_order_id'])
            result = dict((data['job_order_id'][0], data['job_order_id_count']) for data in challan_receive_data)
            val.challan_receipt_count = result.get(self.id, 0)

    def open_challan_receive_history(self):
        action = self.env.ref('job_order_process.action_challan_receipt').read()[0]
        action['domain'] = [('partner_id', '=', self.partner_id.id),('joborder_challan_receipt_lines.job_order_id', '=', self.id)]
        return action

class MypartnerInherit(models.Model):
    _inherit = 'my.partner'

    billing_mode = fields.Boolean('Billing Mode (Each Challan)')

class JobOrderLine(models.Model):
    _name = "job.order.line"

    @api.multi
    def write(self, vals):
        if 'product_id' in vals:
            prod = self.env['my.product'].browse([vals.get('product_id')])
        else:
            prod = self.product_id


        for line in self.env['job.order'].browse([self.order_id.id]).joborder_line:
            if (prod.id == line.product_id.id) and line.id != self.id:
                raise UserError(_(u"Duplicate lines \nthis line already exist!\ncheck your lines again please!"))
        return super(JobOrderLine, self).write(vals)

    @api.model
    def create(self, vals):
        # rec = self.env['job.order'].search([])
        # res=self.env['job.order'].search([('id','in',[16590,16592])])
        # rec=self.env['job.order'].browse([vals['order_id']])
        # print(res,'===')
        for line in self.env['job.order'].browse([vals['order_id']]).joborder_line:
            if (vals.get('product_id') == line.product_id.id) and line.id != self.id:
                raise UserError(_(u"Duplicate lines \nthis line already exist!\ncheck your lines again please!"))
        return super(JobOrderLine, self).create(vals)

    # @api.multi
    # def unlink(self):
    #     if self.env.user.id == self.env.ref('base.user_admin').id:
    #         return super(JobOrderLine, self).unlink()
    #     else:
    #         raise ValidationError('You Can not delete a record')

        @api.multi
        def unlink(self):
            if self.state == 'draft':
                return super(JobOrderLine, self).unlink()
            else:
                if self.state != 'draft' and self.env.user.id == self.env.ref('base.user_admin').id:
                    return super(JobOrderLine, self).unlink()
                else:
                    raise ValidationError('You Can not delete a record')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.unit_id = self.product_id.unit_id.id
            # self.part_id = self.product_id.part_id.id
            self.part_no=self.product_id.part_no
            self.sac_code = self.product_id.category_id.hsn_no
            self.hsn_code = self.product_id.hsn_code
            # self.unit_price = self.product_id.standard_price
            self.tax_id = self.product_id.sale_tax_id.id
            self.process_id = self.product_id.process_name
            # self.surface_area=self.job_order_id.surface_area

    @api.onchange('part_no')
    def onchange_part_id(self):
        if self.part_no:
            product = self.env['my.product'].search([('part_no','=',self.part_no)])
            self.unit_id = product.unit_id.id
            self.product_id = product.id
            self.sac_code = product.category_id.hsn_no
            self.hsn_code = product.hsn_code
            # self.unit_price = product.standard_price
            self.tax_id = product.sale_tax_id.id
            self.per_piece = product.standerd_packing
            self.packing_id = product.per_bin

    def get_subtotal(self):
        total_price = 0.00
        for val in self:
            if val.qty:
                total_price = (val.qty * val.unit_price)
                val.price_subtotal = total_price
    def get_surface_area(self):
        surface_area=0
        for val in self:
            if val.unit_price>0:
                if  val.unit_id==6:
                    if val.process_id.name=='Rplating':
                        val.surface_area=val.unit_price/.1575

    order_id = fields.Many2one('job.order','Id',ondelete='cascade')
    product_id = fields.Many2one('my.product','Product',required=True,)
    # part_id = fields.Many2one('part.number','Part No.')
    part_no=fields.Char('Part No.')
    unit_id = fields.Many2one('my.unit','UOM',required=True)
    qty = fields.Float('Quantity', default=1)

    hsn_code = fields.Char('HSN No.')
    sac_code = fields.Char("SAC Code",default='9988')
    unit_price = fields.Float('Unit Price(Jw)',digits=(16,2))
    material_price=fields.Float('Rate(Material)',digits=(16,2))
    process_id = fields.Many2one('job.process.master',string="Process",required=True,)
    tax_id = fields.Many2one('my.tax', string='Taxes', required=True)
    price_subtotal = fields.Float(compute=get_subtotal, string='Subtotal')
    packing_id = fields.Many2one('standerd.packing',string="Per Item")
    per_piece = fields.Integer('Standerd Packing')
    surface_area = fields.Float('Surface Area(inch²)', digits=(10,2), default=get_surface_area )



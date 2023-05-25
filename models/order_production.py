from odoo import api,models,fields,_
from odoo.exceptions import ValidationError
from datetime import datetime

class JoborderProduction(models.Model):
    _name = 'joborder.production'
    _rec_name = 'batch_no'
    _order = 'id desc'

    # @api.depends('qty')
    def calc_surface_area(self):

        for val in self:
            rec = self.env['joborder.challan.receipt.line'].search(
                [('order_id', '=', val.order_ids.id), ('product_id', '=', val.product_id.id)])
            res = self.env['job.order.line'].search(
                [('order_id', '=', rec.job_order_id.id), ('product_id', '=', val.product_id.id)])

            # print(rec, '==================rec val ==', rec.unit_price)
            if val.qty:
                if res.surface_area == 0:
                    val.surface_area = 0
                else:
                    val.surface_area = (val.qty * res.surface_area)
                    val.value = (val.qty * res.unit_price)

    order_ids = fields.Many2one('joborder.challan.receipt', string="Challan No.",ondelete='cascade')
    product_id = fields.Many2one('my.product', 'Product',required=True)
    # part_id = fields.Many2one('part.number', string='Part No', )
    part_no=fields.Char('Part No.')
    unit_id = fields.Many2one('my.unit', 'UOM')
    qty = fields.Float('Quantity', default=1)

    party_name = fields.Many2one('my.partner', 'Party Name')
    party_date = fields.Date('Date')
    expected_qty = fields.Float('OK Qty')
    rejected_qty = fields.Float('NOT OK Qty')
    remark = fields.Char('Remark')
    production_date = fields.Datetime('Production Date')
    batch_no = fields.Char('Incomeing LOT No.')
    batch_no_prod = fields.Char('Production LOT No.')
    process_ids = fields.Many2one('job.process.master', string="Process")
    rework_qty = fields.Float('Rework Qty')
    inspection_id = fields.Many2one('joborder.inspection')
    inspection_count = fields.Integer('Count', compute="action_view_job_order_inspection")
    invoice_count = fields.Integer('Count', compute="action_view_job_order_challan")
    joborder_challan_receipt_line_id = fields.Integer('Rec Line_id')
    challan_issue_count = fields.Integer('Count',compute="action_view_job_order_challan_issue")
    hold_qty  = fields.Float('Hold Quantity')
    is_hold = fields.Boolean('Hold', default=False)
    surface_area = fields.Integer('Surface Area(in²)',compute='calc_surface_area',)# compute='calc_surface_area',
    value=fields.Float('Value',digits=(10,2),compute='calc_surface_area', )#compute='calc_surface_area',
    # rq=fields.Float('RecQty')
    # mq = fields.Float('MoveQty')
    state = fields.Selection([('draft','Draft'),('confirm','Confirm')],default='draft')
    bq = fields.Float('BalQty')

    # @api.multi
    # def unlink(self):
    #     if self.env.user.id == self.env.ref('base.user_admin').id:
    #         return super(JoborderProduction, self).unlink()
    #     else:
    #         raise ValidationError('You Can not delete a record')
    @api.multi
    def unlink(self):
        if self.state == 'draft':
            return super(JoborderProduction, self).unlink()
        else:
            if self.state != 'draft' and self.env.user.id == self.env.ref('base.user_admin').id:
                return super(JoborderProduction, self).unlink()
            else:
                raise ValidationError('You Can not delete a record')

    def action_move_to_production(self):# update hold qty
        [action] = self.env.ref('job_order_process.action_wizard_move_update_qty_view111').read()
        action['view_mode'] = 'form'
        action['view_mode'] = 'form'
        action['target'] = 'new'
        # self.write({'state':typ})

        return action


    def action_view_job_order_inspection(self):
        contract_data = self.env['joborder.inspection'].sudo().read_group(
            [('production_id', '=', self.id)], ['id'], ['production_id'])
        result = dict((data['production_id'][0], data['production_id_count']) for data in contract_data)
        for employee in self:
            employee.inspection_count = result.get(self.id, 0)

    def open_inspection_history(self):
        action = self.env.ref('job_order_process.action_challan_inspection').read()[0]
        action['domain'] = [('production_id', '=', self.id)]
        return action

    def action_view_job_order_challan(self):
        contract_data = self.env['joborder.challan'].sudo().read_group(
            [('production_challan_reference', '=', self.order_ids.name), ('partner_id', '=', self.party_name.id),
             ('challan_type', '=', 'return'),('challan_line.product_id', '=', self.product_id.id)], ['id'], ['partner_id'])
        result = dict((data['partner_id'][0], data['partner_id_count']) for data in contract_data)
        for employee in self:
            employee.invoice_count = result.get(self.party_name.id, 0)

    def open_partner_history(self):
        action = self.env.ref('job_order_process.action_challan').read()[0]
        action['domain'] = [('production_challan_reference', '=', self.order_ids.name), ('partner_id', '=', self.party_name.id),
             ('challan_type', '=', 'return'),('challan_line.product_id', '=', self.product_id.id)]
        return action

    def action_view_job_order_challan_issue(self):
        contract_data = self.env['joborder.challan'].sudo().read_group([('partner_id', '=', self.party_name.id),('challan_type', '=', 'regular'),('challan_line.product_id', '=', self.product_id.id),('challan_line.party_challan','=',self.order_ids.id)], ['id'],
            ['partner_id'])
        result = dict((data['partner_id'][0], data['partner_id_count']) for data in contract_data)
        for employee in self:
            employee.challan_issue_count = result.get(self.party_name.id, 0)

    def open_challan_issue_history(self):
        action = self.env.ref('job_order_process.action_challan').read()[0]
        action['domain'] = [('partner_id', '=', self.party_name.id),('challan_type', '=', 'regular'),('challan_line.product_id', '=', self.product_id.id),('challan_line.party_challan','=',self.order_ids.id)]
        return action

    def action_return(self):
        rec = self.env['joborder.challan.receipt.line'].search(
            [('order_id', '=', self.order_ids.id), ('product_id', '=', self.product_id.id)])
        res = self.env['joborder.challan']
        res.create({
            'partner_id': self.party_name.id,
            'challan_type': 'return',
            'production_challan_reference': self.order_ids.name,
            'challan_line': [(0, 0,
            {
                'product_id': self.product_id.id,
                'party_challan': self.order_ids.id,
                'qty': self.rejected_qty,
                # 'part_id': self.part_id.id,
                'part_no':self.part_no,
                'unit_id': self.unit_id.id,
                'job_order_id': rec.job_order_id.id,
                'joborder_challan_receipt_line_id': rec.id,
                # 'joborder_challan_receipt_line_id': self.joborder_challan_receipt_line_id,
            })]
        })
        self.is_return = True

    def action_move(self):
        rec = self.env['joborder.inspection']
        rec.create({
            'order_ids': self.order_ids.id,
            'party_name': self.party_name.id,
            'party_date': datetime.strptime(str(self.party_date), '%Y-%m-%d').strftime('%Y-%m-%d'),
            'product_id': self.product_id.id,
            'qty': self.rework_qty,
            # 'part_id': self.part_id.id,
            'part_no':self.part_no,
            'unit_id': self.unit_id.id,
            'batch_no':self.batch_no,
            'inspection_date': self.production_date,
            'process_ids': self.process_ids.id,
            'production_id':self.id,
            'joborder_challan_receipt_line_id': self.joborder_challan_receipt_line_id,

        })
        self.is_inspection = True

    def action_done(self):
        rec = self.env['joborder.challan.receipt.line'].search(
            [('order_id', '=', self.order_ids.id), ('product_id', '=', self.product_id.id)])
        res = self.env['joborder.challan']
        res.create({
            'partner_id': self.party_name.id,
            'challan_type': 'regular',
            #'job_order_challan_reference': self.order_ids.name,
            'challan_line': [(0, 0,
                              {
                                  'product_id': self.product_id.id,
                                  'party_challan': self.order_ids.id,
                                  'qty': self.expected_qty,
                                  # 'part_id': self.part_id.id,
                                  'part_no':self.part_no,
                                  'unit_id': self.unit_id.id,
                                  'job_order_id': rec.job_order_id.id,
                                  'unit_price':rec.unit_price,
                                  'tax_id':rec.tax_id.id,
                                  'joborder_challan_receipt_line_id':rec.id,


                               })]

        })
        self.is_issue = True

    # @api.onchange('expected_qty','rejected_qty','rework_qty')
    # def change_ok_reqork_qty(self):
    #     total = 0
    #     total = self.expected_qty + self.rework_qty + self.rejected_qty
    #     if self.expected_qty and self.rejected_qty and self.rework_qty:
    #         total = self.expected_qty + self.rework_qty + self.rejected_qty
    #         if self.expected_qty > self.qty:
    #             raise  ValidationError(_('Ok qty should not more than the actual quantity'))
    #         if total > self.qty:
    #             raise ValidationError(_('Total quantity should not more than the actual quantity'))
    #         if total < self.qty:
    #             raise ValidationError(_('Total quantity should not less than the actual quantity'))
    # @api.constrains('expected_qty','rejected_qty','rework_qty')
    # def change_ok_reqork_qty(self):
    #     total = 0
    #     total = self.expected_qty + self.rework_qty + self.rejected_qty
    #     if self.expected_qty > self.qty:
    #         raise  ValidationError(_('Ok qty is not more than the actual quantity'))
    #     if total > self.qty:
    #         raise ValidationError(_('Total quantity is not more than the actual quantity'))
    #     if total < self.qty:
    #         raise ValidationError(_('Total quantity is not less than the actual quantity'))

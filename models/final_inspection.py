from odoo import api,models,fields,_
from odoo.exceptions import ValidationError
from datetime import datetime

class JoborderProduction(models.Model):
    _name = 'final.inspection'
    _rec_name = 'batch_no'

    # @api.multi
    # def unlink(self):
    #     if self.env.user.id == self.env.ref('base.user_admin').id:
    #         return super(JoborderFinalInspection, self).unlink()
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
    production_date = fields.Datetime(' Final Inspection Date')
    process_ids = fields.Many2one('job.process.master', string="Process")
    rework_qty = fields.Float('Rework Qty')
    production_id = fields.Many2one('joborder.production')
    batch_no = fields.Char('Batch No.')
    joborder_challan_receipt_line_id=fields.Integer('Rec Line_id')
    is_return = fields.Boolean('is return', default=False)
    is_inspection = fields.Boolean('is_inspection', default=False)
    is_issue = fields.Boolean('is_issue', default=False)
    rw=fields.Float('Rework Qty')
    rtq = fields.Float('Return Qty')
    bq = fields.Float('BalQty')
    surface_area = fields.Integer('Surface Area(in²)',compute='calc_surface_area',)# compute='calc_surface_area',
    value=fields.Float('Value',digits=(10,2),compute='calc_surface_area', )#compute='calc_surface_area',
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], default='draft')

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




    def action_return(self):
        rec = self.env['joborder.challan.receipt.line'].search(
            [('order_id', '=', self.order_ids.id), ('product_id', '=', self.product_id.id)])
        res = self.env['joborder.challan']
        res.create({
            'partner_id': self.party_name.id,
            'payment_term_recs': rec.job_order_id.payment_term,
            'challan_type': 'return',
            'production_challan_reference': self.order_ids.name,
            'challan_line': [(0, 0,
            {
                'product_id': self.product_id.id,
                'name': self.product_id.name,
                'hsn_code': self.product_id.hsn_code,
                'party_challan': self.order_ids.id,
                'qty': self.rejected_qty,
                # 'part_id': line.part_id.id,
                'part_no': self.part_no,
                'unit_id': self.unit_id.id,
                'job_order_id': rec.job_order_id.id,
                'unit_price': 0,
                'material_price': rec.material_price,
                'tax_id': rec.tax_id.id,
                'joborder_challan_receipt_line_id': rec.id,
                'qty_nos': int(self.rejected_qty) if ((self.unit_id.name.lower())[0] == 'n') else 0,
                'qty_kg': self.rejected_qty if ((self.unit_id.name.lower())[0] != 'n') else 0,
                'rtq': self.rejected_qty
            })]
        })
        # print('=============hello rtn========',res)
        self.is_return = True
        self.rtq = self.rtq - self.rejected_qty

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
            'bq': self.rework_qty

        })
        self.is_inspection = True
        self.rw = self.rw - self.rework_qty

    def action_done(self):
        rec = self.env['joborder.challan.receipt.line'].search(
            [('order_id', '=', self.order_ids.id), ('product_id', '=', self.product_id.id)])
        res = self.env['joborder.challan']
        job_work_rec = self.env['job.order.line'].search([('product_id','=',self.product_id.id),('order_id','=',rec.job_order_id.id)])
        # print('=============hello cha issue========', res)
        res.create({
            'partner_id': self.party_name.id,
            'payment_term_recs':rec.job_order_id.payment_term,
            'challan_type': 'regular',
            #'job_order_challan_reference': self.order_ids.name,
            'challan_line': [(0, 0,
                              {
                                  'product_id': self.product_id.id,
                                  'name': self.product_id.name,
                                  'hsn_code': self.product_id.hsn_code,
                                  'party_challan': self.order_ids.id,
                                  'qty': self.expected_qty,
                                  # 'part_id': line.part_id.id,
                                  'part_no': self.part_no,
                                  'unit_id': self.unit_id.id,
                                  'job_order_id': rec.job_order_id.id,
                                  'unit_price':job_work_rec.unit_price,
                                  'material_price': job_work_rec.material_price,
                                  'tax_id': job_work_rec.tax_id.id,
                                  'joborder_challan_receipt_line_id': rec.id,
                                  'qty_nos': int(self.expected_qty) if ((self.unit_id.name.lower())[0] == 'n') else 0,
                                  'qty_kg': self.expected_qty if ((self.unit_id.name.lower())[0] != 'n') else 0,
                                  'bq':self.expected_qty

                               })]


        })
        self.is_issue = True
        self.bq = self.bq - self.expected_qty
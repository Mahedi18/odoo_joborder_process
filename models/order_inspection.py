from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime

from odoo.fields import Char


class JoborderChallanInspection(models.Model):
    _name = 'joborder.inspection'
    _rec_name = 'batch_no'

    order_ids = fields.Many2one('joborder.challan.receipt', string="Challan No.",ondelete='cascade')
    party_date = fields.Date('Challan Date')
    inspection_date = fields.Datetime('Inspection Date')
    product_id = fields.Many2one('my.product', 'Product',required=True)
    part_no=fields.Char('Part No.')
    unit_id = fields.Many2one('my.unit', 'UOM')
    qty = fields.Float('Quantity', default=1,digits=(10,2))
    party_name = fields.Many2one('my.partner', 'Party Name')
    expected_qty = fields.Float('Accepted Qty(Available in Production store)',digits=(16,2))
    rejected_qty = fields.Float('Rejected Qty', readonly=True,digits=(16,2))
    short_quantity = fields.Float('Sort quantity',digits=(16,2))
    osp_qty=fields.Float('OSP Qty',digits=(16,2))
    desp_qty_oldsw=fields.Float('Desp Qty Old Sw',digits=(16,2))
    pending_qty=fields.Float('Pending Quantity',digits=(16,2))
    remark = fields.Char('Remark')
    batch_no = fields.Char('LOT No.')  # type: Char
    process_idsss = fields.Many2one('job.process.master', string="Process")
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('done', 'Done')], string="Status",default="draft")
    insp_line = fields.One2many('joborder.inspection.line', 'insp_id', 'Lines' )
    invoice_count = fields.Integer('Count', compute="action_view_job_order_challan")
    is_return = fields.Boolean('is return',default=False)
    is_osp_issue = fields.Boolean('is Osp Issue', default=False)
    production_count = fields.Integer('Production Count',compute ="action_view_job_order_production")
    production_id = fields.Many2one('final.inspection')
    # joborder_challan_receipt_line_id=fields.Integer('Rec Line_id')
    joborder_challan_receipt_line_id = fields.Many2one('joborder_challan_receipt_line','Rec Line_id')
    remaining_qty = fields.Float('Remaining', readonly=True, digits=(16, 2))
    sq=fields.Float('Short Qty',digits=(16,2))
    bq = fields.Float('BalQty',digits=(16,2))
    rtq=fields.Float('RtnQty',digits=(16,2))

    @api.multi
    def unlink(self):
        if self.env.user.id == self.env.ref('base.user_admin').id:
            return super(JoborderChallanInspection, self).unlink()
        else:
            raise ValidationError('You Can not delete a record')

    def action_view_job_order_production(self):
        contract_data = self.env['joborder.production'].sudo().read_group(
            [('inspection_id', '=', self.id)], ['id'], ['inspection_id'])
        result = dict((data['inspection_id'][0], data['inspection_id_count']) for data in contract_data)
        for employee in self:
            employee.production_count = result.get(self.id, 0)

    def open_production_history(self):
        action = self.env.ref('job_order_process.action_challan_production').read()[0]
        action['domain'] = [('inspection_id', '=', self.id)]
        return action

    def action_view_job_order_challan(self):
        contract_data = self.env['joborder.challan'].sudo().read_group(
            [('job_order_challan_reference', '=', self.order_ids.name),('partner_id', '=', self.party_name.id),
             ('challan_type', '=', 'return'),('challan_line.product_id', '=', self.product_id.id)], ['id'], ['partner_id'])
        result = dict((data['partner_id'][0], data['partner_id_count']) for data in contract_data)
        for employee in self:
            employee.invoice_count = result.get(self.party_name.id,0)

    def open_partner_history(self):
        action = self.env.ref('job_order_process.action_challan').read()[0]
        action['domain'] = [('partner_id', '=', self.party_name.id),('challan_type', '=', 'return'),('job_order_challan_reference', '=', self.order_ids.name),('challan_line.product_id', '=', self.product_id.id)]
        return action

    # def create(self):
    #     print('============create action========')


    def submit(self):
        company_rec = self.env['res.company'].search([])
        for val in company_rec:
            if val.process_mode:
                if self.expected_qty+self.rejected_qty+self.short_quantity+self.osp_qty+self.desp_qty_oldsw == 0:
                    raise ValidationError('Total Sum of Quanitity is not zero')
                if self.expected_qty+self.rejected_qty+self.short_quantity+self.osp_qty+self.desp_qty_oldsw>0:
                    self.state = 'confirm'
                self.action_move_to_production()
                update_rec = self.env['update.qty'].create({
                    'production_qty':self.expected_qty,
                    'production_date': datetime.now().date(),
                    'batch_no': str(self.product_id.id)+'/'+str(self.expected_qty),
                    'inspection_id': self.id,
                })
                # print(update_rec,'=================',update_rec.production_qty)
                update_rec.action_move()
                production_rec = self.env['joborder.production'].search([('inspection_id','=',self.id)])
                # print(production_rec,'==============pro')
                production_rec.action_move_to_production()
                update_hold_rec = self.env['move.update.qty'].create({
                    'expected_qty': production_rec.hold_qty,
                    'rework_qty': 0,
                    'rejected_qty': 0,
                    'remark': 'production done',
                    'production_id': production_rec.id,
                    'total':production_rec.hold_qty
                })
                # print(update_hold_rec,'================',update_hold_rec.total)
                update_hold_rec.action_move()
                production_rec.hold_qty = 0
                if self.rejected_qty:
                    self.action_return()
            else:
                if self.expected_qty+self.rejected_qty+self.short_quantity+self.osp_qty+self.desp_qty_oldsw == 0:
                    raise ValidationError('Total Sum of Quanitity is not zero')
                if self.expected_qty+self.rejected_qty+self.short_quantity+self.osp_qty+self.desp_qty_oldsw>0:
                    self.state = 'confirm'




    # @api.onchange('short_quantity','expected_qty')
    # def change_expected_qty(self):
    #
    #     tqty=0
    #
    #     if self.short_quantity:
    #         qty = self.qty - self.expected_qty - self.short_quantity
    #         if qty < 0:
    #             qty = 0
    #             self.rejected_qty = qty
    #         else:
    #             self.rejected_qty = qty
    #     tqty=self.expected_qty+self.short_quantity+self.rejected_qty
    #     if tqty>0:
    #         self.remark=('Insp.Done: AQ:{0},RQ:{2},SQ:{1}').format(self.expected_qty,self.rejected_qty,self.short_quantity)
    #
    @api.constrains('expected_qty','rejected_qty','short_quantity','desp_qty_oldsw','osp_qty')
    def change_ok_reqork_qty(self):
        total = 0
        total =round( (self.expected_qty + self.short_quantity + self.rejected_qty+self.osp_qty),2)
        qty=round(self.qty,2)
        if round(self.expected_qty,2) > qty:
            raise  ValidationError(_('Ok qty is not more than the actual quantity'))
        if total > qty:
            raise ValidationError(_('Total quantity is not more than the actual quantity'))
        if total < qty:
            raise ValidationError(_('Total quantity is not less than the actual quantity'))
        if self.rejected_qty<0 or self.expected_qty<0 or self.short_quantity<0 :
            # print(self.id,self.expected_qty,self.rejected_qty,self.short_quantity,'=========self.id,self.expected_qty,self.rejected_qty,self.short_quantity,=========')
            raise ValidationError(_(('Total does not match ',self.id,self.expected_qty,self.rejected_qty,self.short_quantity,'=========self.id,self.expected_qty,self.rejected_qty,self.short_quantity,=========')))
        tqty=self.expected_qty+self.short_quantity+self.rejected_qty

        if tqty>0:
            self.remark=('Insp.Done: AQ:{0},RQ:{1},SQ:{2}').format(self.expected_qty,self.rejected_qty,self.short_quantity)
    @api.multi
    def write(self, vals):
        # vals['state'] = 'confirm'
        # rec = self.env['joborder.challan.receipt.line'].search([('id', '=', self.joborder_challan_receipt_line_id)])
        # print(rec, '===================rec')
        if vals.get('expected_qty') or vals.get('short_quantity') or vals.get('rejected_qty'):
            expect_qty = vals.get('expected_qty') if vals.get('expected_qty') else self.expected_qty
            short_qty = vals.get('short_quantity') if vals.get('short_quantity') else self.short_quantity
            osp_qty = vals.get('osp_qty') if vals.get('osp_qty') else self.osp_qty
            desp_qty_oldsw = vals.get('desp_qty_oldsw') if vals.get('desp_qty_oldsw') else self.desp_qty_oldsw

            # rejected_qty = vals.get('rejected_qty') if vals.get('rejected_qty') else self.rejected_qty
            vals['rejected_qty'] = self.qty - expect_qty - short_qty - osp_qty #- desp_qty_oldsw# -pen_qty
            #vals['state'] = 'confirm'
            # vals['rq']=self.qty
        # for data in rec:
        #     print(data.bg, '===================rec')
        #     data.bq = data.bq - self.qty
        #     vals['bq'] = self.qty

        return super(JoborderChallanInspection, self).write(vals)


    def action_move_to_production(self):
        [action] = self.env.ref('job_order_process.action_wizard_update_qty_view111').read()
        action['view_mode'] = 'form'
        action['view_mode'] = 'form'
        action['target'] = 'new'
        # self.write({'state':typ})

        return action



    def action_return(self):
        if self.rejected_qty>0:
            rec = self.env['joborder.challan.receipt.line'].search(
                [('order_id', '=', self.order_ids.id), ('product_id', '=', self.product_id.id)])
            self.bq = self.bq - self.rejected_qty
            self.rtq = self.rejected_qty
            res = self.env['joborder.challan']
            # print(self.joborder_challan_receipt_line_id,'=====33335========')

            res.create({
                'partner_id': self.party_name.id,
                'payment_term_recs': rec.job_order_id.payment_term,
                'challan_type': 'return',
                'job_order_challan_reference': self.order_ids.name,
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
                    'rtq':self.rejected_qty
                }
                                  )]
            })
            # self.write({
            #     # 'mq':self.mq+self.rejected_qty,
            #     'bq':self.bq-self.rejected_qty,
            #     'rtq': self.rejected_qty,
            # })
            self.is_return = True
    def action_osp_issue(self):
        if self.osp_qty>0:
            rec = self.env['joborder.challan.receipt.line'].search(
                [('order_id', '=', self.order_ids.id), ('product_id', '=', self.product_id.id)])
            self.bq = self.bq - self.osp_qty
            # self.osptq = self.osp_qty
            res = self.env['joborder.challan']
            # print(self.joborder_challan_receipt_line_id,'=====33335========')

            res.create({
                'partner_id': self.party_name.id,
                'payment_term_recs': rec.job_order_id.payment_term,
                'challan_type': 'osp',
                'job_order_challan_reference': self.order_ids.name,
                'challan_line': [(0, 0,
                {
                    'product_id': self.product_id.id,
                    'name': self.product_id.name,
                    'hsn_code': self.product_id.hsn_code,
                    'party_challan': self.order_ids.id,
                    'qty': self.osp_qty,
                    # 'part_id': line.part_id.id,
                    'part_no': self.part_no,
                    'unit_id': self.unit_id.id,
                    'job_order_id': rec.job_order_id.id,
                    'unit_price': 0,
                    'material_price': rec.material_price,
                    'tax_id': rec.tax_id.id,
                    'joborder_challan_receipt_line_id': rec.id,
                    'qty_nos': int(self.osp_qty) if ((self.unit_id.name.lower())[0] == 'n') else 0,
                    'qty_kg': self.osp_qty if ((self.unit_id.name.lower())[0] != 'n') else 0,
                    # 'osptq':self.osp_qty
                }
                                  )]
            })
            # self.write({
            #     # 'mq':self.mq+self.rejected_qty,
            #     'bq':self.bq-self.rejected_qty,
            #     'rtq': self.rejected_qty,
            # })
            self.is_osp_issue = True
class JoborderInspectionLines(models.Model):
    _name = 'joborder.inspection.line'

    insp_id = fields.Many2one('joborder.inspection','Id')
    defect_type=fields.Selection([('rust','Rust'),('dent','Dent'),('bur','Bur'),('scratch','Scratch'),
                                  ('oil','Oil'),('threaddamage','Thread Damage'),('sheetpitted','Sheet Pitted'),('others','Others')])
    condition=fields.Selection([('minor','Minor'),('havy','Havy')])
    # minor=fields.Boolean('Minor',default=0)
    # havy=fields.Boolean('Hevy',default=0)
    remarks=fields.Char('Inspection Remark')

    _sql_constraints = [('defect_type_reason', 'unique(defect_type)', 'Already Entered!')]

    # @api.multi
    # def unlink(self):
    #     if self.env.user.id == self.env.ref('base.user_admin').id:
    #         return super(JoborderInspectionLines, self).unlink()
    #     else:
    #         raise ValidationError('You Can not delete a record')
    @api.multi
    def unlink(self):
        if self.state == 'draft':
            return super(JoborderInspectionLines, self).unlink()
        else:
            if self.state != 'draft' and self.env.user.id == self.env.ref('base.user_admin').id:
                return super(JoborderInspectionLines, self).unlink()
            else:
                raise ValidationError('You Can not delete a record')




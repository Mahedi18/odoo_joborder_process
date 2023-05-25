from odoo import api,models,fields,_
from datetime import datetime
from odoo.exceptions import ValidationError

class Reconcilation(models.Model):
    _name = 'reconcilation'

    name = fields.Integer()
    partner_id = fields.Many2one('my.partner','Partner')
    receipt_challan_id = fields.Many2one('joborder.challan.receipt','Receipt Challan Id')
    reconcilation_line_id = fields.One2many('reconcilation.line','reconcile_id','Reconcilation Line Id')
    date = fields.Date('As On Date')

    @api.multi
    def unlink(self):
        if self.env.user.id == self.env.ref('base.user_admin').id:
            return super(Reconcilation, self).unlink()
        else:
            raise ValidationError('You Can not delete a record')

    # @api.multi
    # def write(self, vals):
    #     seq = self.env['ir.sequence'].get('reconcilation')
    #     vals['name'] = seq
    #     res = super(Reconcilation, self).write(vals)
    #     return res
    def action_executequery(self):
        result = self._cr.execute('SELECT product_id,sum(rqty),sum(iqty) FROM(select product_id,qty rqty , 0 iqty  from joborder_challan_receipt_line union all select product_id,0 rqty,qty iqty from challan_line ) ss group by product_id')
        # for e in result:
        #     print(e,'result')
        # # print('result',result)

    def action_fetch(self):
        result = []
        partner_rec = self.env['my.partner'].search([])
        for partner in partner_rec:
            receipt_challan_rec = self.env['joborder.challan.receipt'].search([('partner_id', '=', partner.id),('date','<=',self.date)])
            for rec in receipt_challan_rec:
                for line in rec.joborder_challan_receipt_lines:
                    inspection_rec = self.env['joborder.inspection'].search(
                        [('product_id', '=', line.product_id.id), ('order_ids', '=', line.order_id.id)])
                    production_rec = self.env['joborder.production'].search(
                        [('product_id', '=', line.product_id.id), ('order_ids', '=', line.order_id.id)])
                    final_inspetion_rec = self.env['final.inspection'].search(
                        [('product_id', '=', line.product_id.id), ('order_ids', '=', line.order_id.id)])
                    challan_rec = self.env['challan.line'].search(
                        [('product_id', '=', line.product_id.id), ('party_challan', '=', line.order_id.id)])
                    challan_bill_rec = self.env['challan.bill.line'].search(
                        [('product_id', '=', line.product_id.id), ('party_challan', '=', line.order_id.id)])
                    inspection_bq = sum(data.bq for data in inspection_rec)
                    inspection_sq = sum(val.sq for val in inspection_rec)
                    inspection_rtq = sum(val1.rtq for val1 in inspection_rec)
                    production_bq = sum(val2.bq for val2 in production_rec)
                    final_inspection_bq = sum(val3.bq for val3 in final_inspetion_rec)
                    final_inspection_rtq = sum(val4.rtq for val4 in final_inspetion_rec)
                    final_inspection_rw = sum(val5.rw for val5 in final_inspetion_rec)
                    challan_issue_rtq = sum(val6.rtq for val6 in challan_rec)
                    challan_issue_bq = sum(val7.bq for val7 in challan_rec)
                    challan_bill_bq = sum(val9.bq for val9 in challan_bill_rec)
                    total = line.bq + challan_bill_bq + challan_issue_bq + inspection_bq + inspection_sq + inspection_rtq + production_bq + final_inspection_bq + final_inspection_rtq + final_inspection_rw + challan_issue_rtq
                    result.append((0, 0, {
                        'partner_id':partner.id,
                        'receipt_challan_id':rec.id,
                        'date':rec.date,
                        'product_id': line.product_id.id,
                        'receipt_bq': line.bq,
                        'inspection_bq': inspection_bq,
                        'inspection_sq': inspection_sq,
                        'inspection_rtq': inspection_rtq,
                        'production_bq': production_bq,
                        'final_inspection_bq': final_inspection_bq,
                        'final_inspection_rtq': final_inspection_rtq,
                        'final_inspection_rw': final_inspection_rw,
                        'challan_issue_rtq': challan_issue_rtq,
                        'challan_issue_bq': challan_issue_bq,
                        'challan_bill_bq': challan_bill_bq,
                        'total': total
                    }))
        if self.reconcilation_line_id:
            self.reconcilation_line_id.unlink()
            self.reconcilation_line_id = result
        else:
            self.reconcilation_line_id = result


    @api.onchange('partner_id')
    def onchange_partner_id(self):
        data_list = []
        for val in self.env['joborder.challan.receipt'].search([('partner_id', '=', self.partner_id.id)]):
            data_list.append(val.id)
        domain = {'receipt_challan_id': [('id', 'in', data_list)]}
        # self.name = self.env['ir.sequence'].get('reconcilation')
        return {'domain': domain}  # ,'domain1':domain1

    @api.onchange('receipt_challan_id','partner_id','date')
    def get_line_data(self):
        result = []
        if self.receipt_challan_id:
            self.date = self.receipt_challan_id.date
            for line in self.receipt_challan_id.joborder_challan_receipt_lines:
                inspection_rec = self.env['joborder.inspection'].search([('product_id','=',line.product_id.id),('order_ids','=',line.order_id.id)])
                production_rec = self.env['joborder.production'].search([('product_id', '=', line.product_id.id), ('order_ids', '=', line.order_id.id)])
                final_inspetion_rec = self.env['final.inspection'].search([('product_id', '=', line.product_id.id), ('order_ids', '=', line.order_id.id)])
                challan_iss_rec = self.env['challan.line'].search([('product_id', '=', line.product_id.id),('party_challan','=',line.order_id.id)])
                challan_bill_rec = self.env['challan.bill.line'].search([('product_id', '=', line.product_id.id), ('party_challan', '=', line.order_id.id)])

                inspection_bq = sum(data.bq for data in inspection_rec)
                inspection_sq = sum(val.sq for val in inspection_rec)
                inspection_rtq = sum(val1.rtq for val1 in inspection_rec)
                production_bq = sum(val2.bq for val2 in production_rec)
                final_inspection_bq = sum(val3.bq for val3 in final_inspetion_rec)
                final_inspection_rtq = sum(val4.rtq for val4 in final_inspetion_rec)
                final_inspection_rw = sum(val5.rw for val5 in final_inspetion_rec)
                challan_issue_rtq = sum(val6.rtq for val6 in challan_iss_rec)
                challan_issue_bq = sum(val7.bq for val7 in challan_iss_rec)
                challan_bill_bq = sum(val9.bq for val9 in challan_bill_rec)
                total = challan_bill_bq + challan_issue_bq + inspection_bq + inspection_sq + inspection_rtq + production_bq + final_inspection_bq + final_inspection_rtq + final_inspection_rw + challan_issue_rtq

                result.append((0, 0, {
                    'partner_id':self.partner_id.id,
                    'receipt_challan_id':self.receipt_challan_id.id,
                    'date':self.receipt_challan_id.date,
                    'product_id': line.product_id.id,
                    'receipt_bq': line.bq,
                    'inspection_bq': inspection_bq,
                    'inspection_sq': inspection_sq,
                    'inspection_rtq': inspection_rtq,
                    'production_bq': production_bq,
                    'final_inspection_bq': final_inspection_bq,
                    'final_inspection_rtq': final_inspection_rtq,
                    'final_inspection_rw': final_inspection_rw,
                    'challan_issue_rtq': challan_issue_rtq,
                    'challan_issue_bq': challan_issue_bq,
                    'challan_bill_bq': challan_bill_bq,
                    'total':total
                }))
        else:
            receipt_challan_rec = self.env['joborder.challan.receipt'].search([('partner_id','=',self.partner_id.id),('date','>=',self.date)])
            for rec in receipt_challan_rec:
                for line in rec.joborder_challan_receipt_lines:
                    inspection_rec = self.env['joborder.inspection'].search(
                        [('product_id', '=', line.product_id.id), ('order_ids', '=', line.order_id.id)])
                    production_rec = self.env['joborder.production'].search(
                        [('product_id', '=', line.product_id.id), ('order_ids', '=', line.order_id.id)])
                    final_inspetion_rec = self.env['final.inspection'].search(
                        [('product_id', '=', line.product_id.id), ('order_ids', '=', line.order_id.id)])
                    challan_rec = self.env['challan.line'].search(
                        [('product_id', '=', line.product_id.id), ('party_challan', '=', line.order_id.id)])
                    challan_bill_rec = self.env['challan.bill.line'].search(
                        [('product_id', '=', line.product_id.id), ('party_challan', '=', line.order_id.id)])
                    inspection_bq = sum(data.bq for data in inspection_rec)
                    inspection_sq = sum(val.sq for val in inspection_rec)
                    inspection_rtq = sum(val1.rtq for val1 in inspection_rec)
                    production_bq = sum(val2.bq for val2 in production_rec)
                    final_inspection_bq = sum(val3.bq for val3 in final_inspetion_rec)
                    final_inspection_rtq = sum(val4.rtq for val4 in final_inspetion_rec)
                    final_inspection_rw = sum(val5.rw for val5 in final_inspetion_rec)
                    challan_issue_rtq = sum(val6.rtq for val6 in challan_rec)
                    challan_issue_bq = sum(val7.bq for val7 in challan_rec)
                    challan_bill_bq = sum(val9.bq for val9 in challan_bill_rec)
                    total = challan_bill_bq + challan_issue_bq + inspection_bq + inspection_sq + inspection_rtq + production_bq + final_inspection_bq + final_inspection_rtq + final_inspection_rw + challan_issue_rtq
                    result.append((0, 0, {
                        'partner_id': self.partner_id.id,
                        'receipt_challan_id': rec.id,
                        'date': rec.date,
                        'product_id': line.product_id.id,
                        'receipt_bq': line.bq,
                        'inspection_bq': inspection_bq,
                        'inspection_sq': inspection_sq,
                        'inspection_rtq': inspection_rtq,
                        'production_bq': production_bq,
                        'final_inspection_bq': final_inspection_bq,
                        'final_inspection_rtq': final_inspection_rtq,
                        'final_inspection_rw': final_inspection_rw,
                        'challan_issue_rtq': challan_issue_rtq,
                        'challan_issue_bq': challan_issue_bq,
                        'challan_bill_bq': challan_bill_bq,
                        'total': total
                    }))
        self.reconcilation_line_id = result


class ReconcilationLine(models.Model):
    _name = 'reconcilation.line'

    reconcile_id = fields.Many2one('reconcilation')
    partner_id = fields.Many2one('my.partner','Partner')
    receipt_challan_id = fields.Many2one('joborder.challan.receipt', 'Receipt Challan Id')
    date = fields.Date('Date' ,default=datetime.today())
    product_id = fields.Many2one('my.product', 'Product')
    receipt_bq = fields.Float('Receipt Bal Qty')
    inspection_bq = fields.Float('Inspection Bal Qty')
    inspection_sq = fields.Float('Inspection Sort Qty')
    inspection_rtq = fields.Float('Inspection Return Qty')
    production_bq = fields.Float('Production Bal Qty')
    final_inspection_bq = fields.Float('Final Inspection Bal Qty')
    final_inspection_rw = fields.Float('Final Inspection Rework Qty')
    final_inspection_rtq = fields.Float('Final Inspection Return Qty')
    challan_issue_bq = fields.Float('challan issue bal qty')
    challan_issue_rtq = fields.Float('challan issue return qty')
    challan_bill_bq = fields.Float('challan bill bal qty')
    total = fields.Float('Total')

    @api.multi
    def unlink(self):
        if self.env.user.id == self.env.ref('base.user_admin').id:
            return super(ReconcilationLine, self).unlink()
        else:
            raise ValidationError('You Can not delete a record')

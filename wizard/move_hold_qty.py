from odoo import api, models, fields,_
from datetime import datetime
from odoo.exceptions import ValidationError


class updateproductqty(models.Model):
    _name = 'move.update.qty'

    expected_qty = fields.Float('Ok Quantity',readonly=False)
    rework_qty = fields.Float('Rework Quantity')
    rejected_qty = fields.Float('Not Ok Quantity')
    total = fields.Float('Total')
    remark = fields.Char('Remark')
    production_id = fields.Many2one('joborder.production')

    @api.constrains('expected_qty','rejected_qty','rework_qty')
    def change_ok_reqork_qty(self):
        total1 = 0
        total1 = self.expected_qty + self.rework_qty + self.rejected_qty
        self.total = self.expected_qty + self.rework_qty + self.rejected_qty
        active_rec = self._context.get('active_id', [])
        production_rec = self.env['joborder.production']
        data = production_rec.browse(active_rec)
        if self.production_id:
            data = self.production_id
        if total1 > data.qty:
            raise ValidationError(_('Total quantity is not more than the actual quantity'))

    def action_move(self):
        print('========================')
        active_rec = self._context.get('active_id', [])
        production_rec = self.env['joborder.production']
        data = production_rec.browse(active_rec)
        if self.production_id:
            data = self.production_id
        # data.expected_qty = self.expected_qty
        # data.rework_qty = self.rework_qty
        # data.rejected_qty = self.rejected_qty
        # data.hold_qty = data.qty - self.total
        # data.remark = ('Production.Done: AQ:{0},RQ:{1},RQ:{2},HQ:{3}').format(data.expected_qty, data.rejected_qty,
        #                                                          data.rework_qty,data.hold_qty)
        # if self.production_qty > data.expected_qty:
        #     raise ValidationError(_('Actual quantity is not less than the production quantity'))
        if data.hold_qty > 0:
            if self.total > data.hold_qty:
                raise ValidationError(_('Total quantity is not more than the hold quantity'))
        for val in data:
            final_production_rec = self.env['final.inspection']
            final_production_rec.create({
                'order_ids': val.order_ids.id,
                'party_name': val.party_name.id,
                'party_date': datetime.strptime(str(val.party_date), '%Y-%m-%d').strftime('%Y-%m-%d'),
                'product_id': val.product_id.id,
                'qty': self.total,
                # 'part_id': val.part_id.id,
                'part_no':val.part_no,
                'unit_id': val.unit_id.id,
                'production_date': datetime.now(),
                'process_ids': val.process_ids.id,
                'production_id': data.id,
                'expected_qty':self.expected_qty,
                'rework_qty': self.rework_qty,
                'rejected_qty': self.rejected_qty,
                'batch_no':val.batch_no,
                'joborder_challan_receipt_line_id':val.joborder_challan_receipt_line_id,
                'bq': self.expected_qty,
                'rtq':self.rejected_qty,
                'rw':self.rework_qty,
                'remark':val.batch_no_prod,
            })

            # check_inspection_id = final_production_rec.search([('production_id', '=', data.id)])
            # prev_production_qty = ([ins.qty for ins in check_inspection_id])

            val.hold_qty = val.hold_qty - self.total
            val.bq = val.bq - (self.expected_qty + self.rejected_qty + self.rework_qty)

            if val.hold_qty == 0:
                val.is_hold = True
            if val.bq == 0:
                val.state = 'confirm'
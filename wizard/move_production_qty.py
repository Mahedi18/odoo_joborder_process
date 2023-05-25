from odoo import api, models, fields,_
from datetime import datetime
from odoo.exceptions import ValidationError


class updateproductqty(models.Model):
    _name = 'update.qty'

    production_qty = fields.Float('Quantity', readonly=False,required=True)
    production_date = fields.Datetime('Production Date',default=lambda self: fields.datetime.now())
    batch_no = fields.Char('Production Batch No.')
    inspection_id = fields.Many2one('joborder.inspection')

    @api.model
    def default_get(self, fields_list):
        res = super(updateproductqty,self).default_get(fields_list)
        active_rec = self._context.get('active_id', [])
        inspection_rec = self.env['joborder.inspection']
        data = inspection_rec.browse(active_rec)
        res['inspection_id'] = data.id
        res['batch_no'] = 'NEC/' + str(data.product_id.id) + '/'+str(data.expected_qty)
        res['production_qty'] = data.expected_qty
        return res

    sql_constraints = [
        ('unique(batch_no)', 'Batch No. already exists!')
    ]


    def action_move(self):
        active_rec = self._context.get('active_id', [])
        inspection_rec = self.env['joborder.inspection']
        data = inspection_rec.browse(active_rec)
        if self.inspection_id:
            data = self.inspection_id
        print(self.production_qty,'=====================',data.expected_qty)
        if self.production_qty > data.expected_qty:
            raise ValidationError(_('Actual quantity is not less than the production quantity'))
        if data.remaining_qty > 0:
            if self.production_qty > data.remaining_qty:
                raise ValidationError(_('Production quantity is not more than the remaning quantity'))
        for val in data:
            production_rec = self.env['joborder.production']

            production_rec.create({
                'order_ids': val.order_ids.id,
                'party_name': val.party_name.id,
                'party_date': datetime.strptime(str(val.party_date), '%Y-%m-%d').strftime('%Y-%m-%d'),
                'product_id': val.product_id.id,
                'qty': self.production_qty,
                # 'part_id': val.part_id.id,
                'part_no':val.part_no,
                'unit_id': val.unit_id.id,
                'production_date': self.production_date,
                'process_ids': val.process_idsss.id,
                'batch_no_prod':self.batch_no,
                'batch_no':self.inspection_id.batch_no,
                'inspection_id': data.id,
                'joborder_challan_receipt_line_id':data.joborder_challan_receipt_line_id,
                'hold_qty':self.production_qty,
                'bq':self.production_qty

            })

            check_inspection_id = production_rec.search([('inspection_id', '=', data.id)])

            prev_production_qty = sum([ins.qty for ins in check_inspection_id])

            val.remaining_qty = val.expected_qty - prev_production_qty
            val.bq = val.bq-self.production_qty

            if val.remaining_qty == 0:
                val.state = 'done'

            # if val.remaining_qty > 0:
            #     val.remaining_qty = val.remaining_qty - self.production_qty
            #     production_rec.create({
            #         'order_ids': val.order_ids.id,
            #         'party_name': val.party_name.id,
            #         'party_date': datetime.strptime(str(val.party_date), '%Y-%m-%d').strftime('%Y-%m-%d'),
            #         'product_id': val.product_id.id,
            #         'qty': val.expected_qty,
            #         'part_id': val.part_id.id,
            #         'unit_id': val.unit_id.id,
            #         'production_date': datetime.now(),
            #         'process_ids': val.process_ids.id,
            #         'batch_no': 'PRO' + '/' + datetime.strptime(str(datetime.now().date()), '%Y-%m-%d').strftime(
            #             '%Y-%m-%d') + '/' + self.env['ir.sequence'].get('joborder_production')
            #     })
            # val.state = 'done'

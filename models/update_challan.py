from odoo import api,models,fields,_
from datetime import datetime
class updatechallan(models.TransientModel):
    _name = 'update.challan'

    def update_challan_receipt(self):
        # challan_receive_rec = self.env['joborder.challan.receipt'].search([])
        challan_rec = self.env['joborder.challan.receipt'].search([('state', '=', 'draft')], limit=2000)
        # print(challan_rec, '==================challan rec')
        for rec in challan_rec:
            self.env.cr.autocommit(False)
            try:
                # print(rec, '=====================before')
                rec.action_confirm()
                # print(rec, '================after')
                self.env.cr.commit()
            except:
                self.env.cr.rollback()
            finally:
                self.env.cr.autocommit(True)

    def update_auto_inspection(self):
        inspection_rec = self.env['joborder.inspection'].search([('state', '=', 'draft'),('id','=',66999)])
        for val in inspection_rec:
            if val.product_id.itemgroup_id.name=='Packing':
                val.rejected_qty=val.qty
                val.bq=0
                val.remark = 'New Packing Product Insp Done Auto'
                val.state = 'done'
            elif val.product_id.itemgroup_id.name=='FINISHED GOODS':
                val.expected_qty=val.qty
                val.bq=0
                val.remark = 'New Jobwork Product Insp Done Auto'
                val.state = 'done'

    def update_challan_issue(self):
        challan_receive_rec = self.env['joborder.challan.receipt'].search([])
        challan_rec = self.env['joborder.challan'].search([('state','=','draft')],limit=1000)
        # print(challan_rec,'==================challan rec')
        for rec in challan_rec:
            self.env.cr.autocommit(False)
            try:
                # print(rec, '=====================before')
                rec.action_confirm()
                # print(rec, '================after')
                self.env.cr.commit()
            except:
                self.env.cr.rollback()
            finally:
                self.env.cr.autocommit(True)
        for data in challan_receive_rec:
            self.env.cr.autocommit(False)
            try:
                # print(rec, '=====================before')
                data._total_issue()
                # print(rec, '================after')
                self.env.cr.commit()
            except:
                self.env.cr.rollback()
            finally:
                self.env.cr.autocommit(True)







    def update_auto_production(self):

        # challan_receive_rec = self.env['joborder.challan.receipt'].search([])
        # challan_rec = self.env['joborder.challan.receipt'].search([('state', '=', 'draft')], limit=2000)
        inspection_rec = self.env['joborder.inspection'].search([('state', '=', 'draft'),('order_ids','=',26369)])

        production_rec = self.env['joborder.production']
        # print(inspection_rec, '==================challan rec')
        for val in inspection_rec:
            # print(val.id, '==================inspection rec',val.expected_qty)

            production_rec.create({
                'order_ids': val.order_ids.id,
                'party_name': val.party_name.id,
                'party_date': datetime.strptime(str(val.party_date), '%Y-%m-%d').strftime('%Y-%m-%d'),
                'product_id': val.product_id.id,
                'qty': val.qty,
                # 'part_id': val.part_id.id,
                'part_no':val.part_no,
                'unit_id': val.unit_id.id,
                'production_date': datetime.strptime(str(val.party_date), '%Y-%m-%d').strftime('%Y-%m-%d'),
                'process_ids': val.process_ids.id,
                'batch_no':0.00,
                'production_id': val.id,
                'joborder_challan_receipt_line_id':val.joborder_challan_receipt_line_id,
                'hold_qty':val.expected_qty,
                'bq':val.expected_qty,
                # 'state':'confirm'
                 })

            #     print(val, '=====================before')
            val.state='confirm'
            # val.action_confirm()
            #     print(val, '================after')
            #     self.env.cr.commit()
            # except:
            #     self.env.cr.rollback()
            # finally:
            #     self.env.cr.autocommit(True)
    # def action_move(self):
    #     active_rec = self._context.get('active_id', [])
    #     inspection_rec = self.env['joborder.inspection']
    #     data = inspection_rec.browse(active_rec)
    #     if self.production_qty > data.expected_qty:
    #         raise ValidationError(_('Actual quantity is not less than the production quantity'))
    #     if data.remaining_qty > 0:
    #         if self.production_qty > data.remaining_qty:
    #             raise ValidationError(_('Production quantity is not more than the remaning quantity'))
    #     for val in data:
    #         production_rec = self.env['joborder.production']
    #
    #         production_rec.create({
    #             'order_ids': val.order_ids.id,
    #             'party_name': val.party_name.id,
    #             'party_date': datetime.strptime(str(val.party_date), '%Y-%m-%d').strftime('%Y-%m-%d'),
    #             'product_id': val.product_id.id,
    #             'qty': self.production_qty,
    #             # 'part_id': val.part_id.id,
    #             'part_no':val.part_no,
    #             'unit_id': val.unit_id.id,
    #             'production_date': self.production_date,
    #             'process_ids': val.process_ids.id,
    #             'batch_no':self.batch_no,
    #             'inspection_id': data.id,
    #             'joborder_challan_receipt_line_id':data.joborder_challan_receipt_line_id,
    #             'hold_qty':self.production_qty,
    #             'bq':self.production_qty
    #
    #         })



import time
from odoo import api, fields, models
from datetime import datetime,timedelta
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning


import logging
_logger = logging.getLogger(__name__)


class IssueMaterial(models.TransientModel):
    _name = 'issue.material'

    issue_material_line = fields.One2many('issue.material.line', 'material_id', 'Lines')

    @api.model
    def default_get(self, fields):
        obj = self.env['joborder.challan.receipt'].browse(self.env.context.get('active_id'))
        res = super(IssueMaterial, self).default_get(fields)
        moves = []
        res = {}
        if 'issue_material_line' in fields:
            query = "select bol.id , bol.product_id, bol.qty_remaining, bol.uom_id, bol.hsn_code, bol.unit_price,bol.tax_id from Joborder_challan_receipt_line as bol left join joborder_challan_receipt as bo on bo.id = bol.order_id where  bo.id = '" + str(obj.id) + "'"
            self.env.cr.execute(query)
            temp = self.env.cr.fetchall()
            for val1 in temp:
                if val1[2]:

                    dict2 = {}
                    dict2['material_id'] =val1[0]
                    dict2['product_id']=val1[1]
                    dict2['qty'] = val1[2]
                    dict2['uom_id']=val1[3]
                    dict2['hsn_code']=val1[4]
                    dict2['unit_price']=val1[5]
                    dict2['tax_id'] = val1[6]


                    moves.append (dict2)
            res['issue_material_line'] = [(0, 0, x) for x in moves]
        return res


    def material_issue(self):
        product_list = []
        product_list1 = []
        joborder = self.env['joborder.challan.receipt'].browse(self.env.context.get('active_id'))
        challan = self.env['joborder.challan'].create({'challan_id': joborder.id,'origin':joborder.id,
                                                       'partner_id': joborder.partner_id.id,
                                                       'date': datetime.today().strftime(
                                                           '%Y-%m-%d')})
        for val in self.issue_material_line:
            if val.select:

                self.env['challan.line'].create(
                                                {'order_id': challan.id,
                                                'product_id': val.product_id.id,
                                                 'party_challan':joborder.id,
                                                'uom_id': val.uom_id.id,
                                                'unit_price': val.unit_price,
                                                'hsn_code': val.product_id.category_id.hsn_no,
                                                'qty': val.qty,
                                                 'tax_id': val.tax_id.id})



                job_obj = self.env['joborder.challan.receipt.line'].search(
                                                            [('order_id', '=', joborder.id),
                                                             ('product_id', '=', val.product_id.id)])
                for job in job_obj:
                    job.write({'issue_qty': job.issue_qty + val.qty})
                #
                #
                # product_list = self.env['stock.quant'].search( [
                #         ('product_id', '=', val.product_id.id,),
                #         ('location_id', '=', joborder.location_id.id)])
                # if product_list:
                #     for val6 in product_list:
                #         val6.write(
                #                 {'quantity': val6.quantity - val.qty})
                # else:
                #     self.env['stock.quant'].create({'product_id': val.product_id.id,
                #                                                         'location_id': joborder.location_id.id,
                #                                                         'quantity': - val.qty,
                #                                                         'product_uom_id':val.uom_id.id
                #
                #                                                         })
                #
                # product_list1 = self.env['stock.quant'].search([
                #         ('product_id', '=', val.product_id.id,),
                #         ('location_id', '=', joborder.location_dest_id.id)])
                # if product_list1:
                #     for val7 in product_list1:
                #         val7.write(
                #                 {'quantity': val7.quantity + val.qty})
                # else:
                #     self.env['stock.quant'].create({'product_id': val.product_id.id,
                #                                                         'location_id': joborder.location_dest_id.id,
                #                                                         'quantity': val.qty,
                #                                                         'product_uom_id':val.uom_id.id
                #
                #                                                         })



        return {
                        'name': ('Challan'),
                        'type': 'ir.actions.act_window',
                        'res_model': 'joborder.challan',
                        'res_id': challan.id,
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target': 'current',
                        'nodestroy': True,
                    }








class IssueMaterialLine(models.TransientModel):
    _name = 'issue.material.line'


    material_id = fields.Many2one('issue.material', 'Wizard')
    select = fields.Boolean('Select')
    product_id = fields.Many2one('my.product', 'Product')
    unit_price = fields.Float('Unit Price')
    uom_id = fields.Many2one('my.uom', 'UOM')
    qty = fields.Float('Quantity')
    hsn_code = fields.Char('Hsn Code')
    tax_id = fields.Many2one('my.tax', string='Taxes', )

from odoo import api,models,fields,_

class ChallanReceiptLineWizard(models.TransientModel):
    _name = 'challan.line.wizard.receipt'

    def _get_receipt_lines(self):
        challan_id = self.env['joborder.challan'].search([('id','=',self._context.get('active_id',False))])
        rec = self.env['joborder.challan.receipt.line'].search([('order_id.partner_id', '=', challan_id.partner_id.id)])
        return rec

    receipt_wizard_id = fields.Many2many('joborder.challan.receipt.line',string="Id",default=_get_receipt_lines)
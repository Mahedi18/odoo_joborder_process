from odoo import api, fields, models

class JobCard(models.Model):
    _name = 'jobcard'
    _rec_name = 'name'
    # _description = 'New Description'

    def compute_qunatities(self):
        for val in self:
            qty_ins = 0
            qty_pro = 0
            qty_final_ins = 0
            qty_iss = 0
            inspection_rec = self.env['joborder.inspection'].search([('batch_no','=',val.name)])
            production_rec = self.env['joborder.production'].search([('batch_no', '=', val.name)])
            final_inspection_rec = self.env['final.inspection'].search([('batch_no', '=', val.name)])
            challan_issue_rec = self.env['challan.line'].search([('batch_no', '=', val.name)])
            for rec1 in inspection_rec:
                qty_ins += rec1.expected_qty
            for rec2 in production_rec:
                qty_pro += rec2.expected_qty
            for rec3 in final_inspection_rec:
                qty_final_ins += rec3.expected_qty
            for rec4 in challan_issue_rec:
                qty_iss += rec4.qty
            val.qty_insp = qty_ins
            val.qty_prod = qty_pro
            val.qty_finsp = qty_final_ins
            val.qty_iss = qty_iss
            val.qty_bal=val.qty_rec-val.qty_iss
            if val.qty_bal==0:
                val.state='confirm'

    name = fields.Char('Imcoming Lot. No',required=True)
    rec_date = fields.Date('Insp.Date')
    Partner_id=fields.Many2one('my.partner')
    part_no=fields.Char('Part No')
    challan_no=fields.Many2one('Challan No.')
    challan_date=fields.Date('Ch.Date & Time')
    process_id = fields.Many2one('job.process.master', string='Process')
    batch_no_prod=fields.Char('Prod. Batch No.')
    prod_date=fields.Date('Prod Date')
    prod_date = fields.Date('FI Date')
    prduct_id=fields.Many2one('my.product')
    qty_rec=fields.Float(string="Qty Received",digits=(10,2))
    qty_insp=fields.Float(string="Qty Insp",digits=(10,2),compute='compute_qunatities')
    qty_prod=fields.Float(string="Qty Prod",digits=(10,2),compute='compute_qunatities')
    qty_finsp=fields.Float(string="Qty Final Insp",digits=(10,2),compute='compute_qunatities')
    qty_iss=fields.Float(string="Qty Issue",digits=(10,2),compute='compute_qunatities')
    joborder_challan_receipt_line_id=fields.Many2one('joborder.challan.receipt.line',string='Ch.No.')
    qty_bal=fields.Float('Balance Qty',compute='compute_qunatities')


    state = fields.Selection([('open', 'Open'), ('close', 'Close')], default='open')

    # production_line_ids = fields.One2many(comodel_name="jobcard.production", inverse_name="production_line_id", string="Production Details", required=False, )

# class JobCardProduction(models.Model):
#     _name = 'jobcard.production'
#     _rec_name = 'name'
#     # _description = 'New Description'
#
#     name = fields.Char('Batch No.')
#     production_line_id=fields.Many2one('joborder.production')
#     process_id = fields.Many2one('job.process.master', string='Process')
#     date=fields.Date('Date')
#     qty_prod=fields.Float('Production Qty')
#
# class JobCardFinalInspection(models.Model):
#     _name = 'jobcard.final.inspection'
#     _rec_name = 'name'
#     # _description = 'New Description'
#
#     name = fields.Char('Prod. Batch No.')
#     finalinspection_line_id=fields.Many2one('joborder.final.inspection')
#     process_id = fields.Many2one('job.process.master', string='Process')
#     date=fields.Date('Insp. Date')
#     qty_insp=fields.Float('FinalInsp Qty')
#     qty_ok=fields.Float('FinalInsp Qty')
#     qty_ng=fields.Float('NG Qty')
#     qty_rework=fields.Float('Rework Qty')
#
# class JobCardChallanIssue(models.Model):
#     _name = 'jobcard.challan.issue'
#     _rec_name = 'name'
#     # _description = 'New Description'
#
#     name = fields.Char('Batch No.')
#     challan_issue_line_id=fields.Many2one('challan.line')
#     process_id = fields.Many2one('job.process.master', string='Process')
#     date=fields.Date('Date')
#     qty_prod=fields.Float('FinalInsp Qty')
#
#

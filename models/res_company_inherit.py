from odoo import api,models,fields

class ResCompamyInherit(models.Model):
    _inherit = 'res.company'

    iso_logo = fields.Binary('Iso Logo')
    description = fields.Char('Description')
    other_txt=fields.Char('Other Desc')
    process_mode=fields.Boolean('Process Mode (Auto)')

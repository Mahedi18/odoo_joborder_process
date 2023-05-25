from odoo import api,models,fields


class ResUserInheriit(models.Model):
 _inherit = 'res.users'
 # we inherited res.groups model which is Odoo/OpenERP built in model and created two fields in that model.
 remarks = fields.Char(string="Remarks")
 odoobot_state=fields.Char(default='not_initialized')
 # field_2 = fields.Boolean(default=False,string="Field Two")
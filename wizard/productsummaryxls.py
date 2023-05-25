from odoo import models,fields,api

import datetime
from io import BytesIO

import xlwt,  base64

class JobReport(models.AbstractModel):
    _name = 'productsummary_xlsx'
    # _inherit = 'report.report_xlsx.abstract'


# Define one field that temporary hold data for download

    file = fields.Binary('XLS File', readonly=True)






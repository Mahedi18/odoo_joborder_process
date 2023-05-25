from odoo import models
import base64
import io
import logging
import requests
import werkzeug.utils

from PIL import Image
from odoo import http, tools, _
from odoo.http import request
from werkzeug.urls import url_encode
import datetime

class JobReport(models.AbstractModel):
    _name = 'report.custom_invoice.job_ticket_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, obj):
        search_parem = []
        if obj.challan_type:
            if obj.challan_type != 'all':
                search_parem.append(('challan_type', '=', obj.challan_type))
        if obj.party_challan:
            search_parem.append(('name', '=', str(obj.party_challan.name)))
        if obj.from_date:
            search_parem.append(('date', '>=', obj.from_date))
        if obj.to_date:
            search_parem.append(('date', '<=', obj.to_date))
        if obj.partner_id:
            search_parem.append(('partner_id', '=', obj.partner_id.id))
        if obj.product_id:
            search_parem.append(('joborder_challan_receipt_lines.product_id','=',obj.product_id.id))
        challan_rec = self.env['joborder.challan.receipt'].search(search_parem)
        address = self.env.user.company_id.street + ',' + str(self.env.user.company_id.street2) + ',' + str(
            self.env.user.company_id.city) + ',' + str(self.env.user.company_id.state_id.name) + ',' + str(
            self.env.user.company_id.zip)
        address_size_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',

        })
        merge_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': 'red',
            'font_color': 'white',
            'border_color': 'black'
        })
        row = 3
        i=1
        header_row = 1
        col = 0
        new_row = row + 1
        y = 'Yes'
        n = 'No'
        worksheet = workbook.add_worksheet('Custom Invoice')
        worksheet.set_column('A:I', 25)
        worksheet.merge_range('A%s:I%s' % ((1), (1)), address)
        worksheet.merge_range('A%s:I%s' % ((2), (2)), 'Stock Register for the period of' + ' ' + str(obj.from_date) + ' '+'to'+ ' '+str(obj.to_date),address_size_format)
        worksheet.write('A%s' % (row), 'Receive CHALLAN NO.',merge_format)
        worksheet.write('B%s' % (row), 'DATE',merge_format)
        worksheet.write('C%s' % (row), 'Product NAME',merge_format)
        worksheet.write('D%s' % (row), 'Receive QUANTITY',merge_format)
        worksheet.write('E%s' % (row), 'Issue Challan No.',merge_format)
        worksheet.write('F%s' % (row), 'Date',merge_format)
        worksheet.write('G%s' % (row), 'Product NAME',merge_format)
        worksheet.write('H%s' % (row), 'Issue Quantity',merge_format)
        worksheet.write('I%s' % (row), 'Balance Quantity',merge_format)
        for line in challan_rec:
            worksheet.merge_range('A%s:I%s' % ((new_row), (new_row)), line.partner_id.name)
            new_row += 1
            count = 1
            for data in line.joborder_challan_receipt_lines:
                total = data.qty
                if obj.product_id.id:
                    job_rec = self.env['challan.line'].search([('party_challan.name','=',line.name),('product_id','=',obj.product_id.id)])
                else:
                    job_rec = self.env['challan.line'].search([('party_challan.name', '=', line.name)])
                if job_rec:
                    a = 0
                    for val in job_rec:
                        if not val.challan_reciept_id:
                            if data.product_id.id == val.product_id.id:
                                if count == 1:
                                    worksheet.write('A%s' % (new_row), line.name)
                                    worksheet.write('B%s' % (new_row), (datetime.datetime.strptime(str(line.date),'%Y-%m-%d').strftime('%d-%m-%Y')))
                                if a != i:
                                    #total = data.qty - val.qty
                                    worksheet.write('C%s' % (new_row), data.product_id.name)
                                    worksheet.write('D%s' % (new_row), data.qty)
                                    a = i
                                worksheet.write('E%s' % (new_row), val.order_id.name)
                                worksheet.write('F%s' % (new_row), (datetime.datetime.strptime(str(val.order_id.date),'%Y-%m-%d').strftime('%Y-%m-%d')))
                                worksheet.write('G%s' % (new_row), val.product_id.name)
                                worksheet.write('H%s' % (new_row), val.qty)
                                total = total - val.qty
                                worksheet.write('I%s' % (new_row), total)
                                new_row+=1
                                count+=1
                if not job_rec:
                    worksheet.write('A%s' % (new_row), line.name)
                    worksheet.write('B%s' % (new_row),(datetime.datetime.strptime(str(line.date), '%Y-%m-%d').strftime('%d-%m-%Y')))
                    worksheet.write('C%s' % (new_row), data.product_id.name)
                    worksheet.write('D%s' % (new_row), data.qty)
                    worksheet.write('E%s' % (new_row), '')
                    worksheet.write('F%s' % (new_row),'')
                    worksheet.write('G%s' % (new_row), '')
                    worksheet.write('H%s' % (new_row), '')
                    worksheet.write('I%s' % (new_row), data.qty)
                    new_row += 1













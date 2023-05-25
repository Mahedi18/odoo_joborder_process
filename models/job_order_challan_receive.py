from odoo import api, fields, models,_
from datetime import datetime, timedelta
import math
from odoo.exceptions import UserError, ValidationError

class JoborderChallanReceipt(models.Model):
    _name = "joborder.challan.receipt"
    _order = 'mast_oldid desc'

    def action_generate(self):
        return dict(
            report_name='custom_invoice.job_challan_receipt_xlsx',
            report_type='xlsx',
            type='ir.actions.report',
        )
    def get_data(self):
        data_list = []
        for val in self.joborder_challan_receipt_lines:
            value1 = val.qty
            for data in range(0,val.no_of_bin):
                data_rec = {}
                data_rec['product_name'] = val.product_id.name
                data_rec['part_no'] = val.part_no
                data_rec['qty'] = val.per_piece if (value1-val.per_piece)>0 else value1
                data_rec['lot'] = val.batch_no
                data_rec['next'] = val.process.name
                data_rec['batch'] = val.batch_no
                value = value1 - val.per_piece  # 100
                value1 = value
                inspection_rec = self.env['joborder.inspection'].search([('order_ids.name','=',self.name)])
                for line in inspection_rec:
                    data_rec['inspection_batch'] = line.batch_no
                    data_rec['inspection_date'] = line.inspection_date
                    data_rec['inspection_qty'] = line.expected_qty
                data_list.append(data_rec)
        return data_list
    def open_wiz(self):
        view = self.env.ref('job_order_process.view_issue_material')
        return {
            'name': ('Issur Material'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'issue.material',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': self.env.context,
        }
    def action_done(self):
        self.write({'state': 'done'})
    def action_confirm(self):
        res = self.env['joborder.inspection']
        jobcard_rec = self.env['jobcard']
        tot=0.00
        for line in self.joborder_challan_receipt_lines:
            line.bal_qtynew=round(line.qty,2)
            # print(line.process,'=============',line.process.name)
            # val.write({'bal_qtynew': val.remaining_qty})
            ins_rec = res.create({
                        'joborder_challan_receipt_line_id':line.id,
                        'order_ids':line.order_id.id,
                        'party_name':line.order_id.partner_id.id,
                        'party_date':datetime.strptime(str(line.order_id.date),'%Y-%m-%d').strftime('%Y-%m-%d'),
                        'product_id':line.product_id.id,
                        'qty':round(line.qty,2),
                        # 'expected_qty':round(line.qty,2) if line.process.name == 'Rplating' or line.process.name == 'CED' or line.process.name == 'Bplating' else 0,
                        # 'rejected_qty':round(line.qty,2) if line.process.name != 'Rplating' or line.process.name != 'CED' or line.process.name != 'Bplating' else 0,
                        'part_no':line.part_no,
                        'unit_id':line.unit_id.id,
                        'inspection_date':datetime.now(),
                        'process_idsss':line.process.id,
                        'batch_no': line.batch_no,
                        'bq':round((line.qty-line.osp_qty-line.desp_qty_oldsw),2),
            })
            job_rec = jobcard_rec.create({
                'joborder_challan_receipt_line_id':line.id,
                'rec_date':datetime.now().date(),
                'Partner_id': line.order_id.partner_id.id,
                'product_id': line.product_id.id,
                'part_no': line.part_no,
                'unit_id': line.unit_id.id,
                'process_id': line.process.id,
                'name': line.batch_no,
                'qty_rec':line.qty
            })
            # print(ins_rec,'===============insss')
            if line.process.name == 'Rplating' or line.process.name == 'CED' or line.process.name == 'Bplating':
                ins_rec.expected_qty = ins_rec.qty
                ins_rec.rejected_qty = 0
            else:
                ins_rec.rejected_qty = ins_rec.qty
                ins_rec.expected_qty = 0
            tot=tot+line.qty
        # print(res,'=================',res.expected_qty,'============',res.rejected_qty)
        # if res.process_idsss.name == 'Rplating' or res.process_idsss.name == 'Bplating' or res.process_idsss.name == 'CED':
        #     res.expected_qty = res.qty
        # else:
        #     res.rejected_qty = res.qty
        self.write({'state': 'confirm','total_rec':tot,'total_iss':0,'total_bal':tot})
        return True
    def _amount_all_wrapper(self):
        total_amount = 0.00
        for val in self:
            if val.joborder_challan_receipt_lines:
                for val1 in val.joborder_challan_receipt_lines:
                    total_amount = total_amount + val1.price_subtotal
                    self.amount_untaxed = total_amount
    def _tax_amount(self):
        total_tax = 0.00
        for val in self:
            if val.joborder_challan_receipt_lines:
                for val1 in val.joborder_challan_receipt_lines:
                    amount = 0.0
                    if val1.tax_id:
                        amount = amount + val1.tax_id.amt
                    total_tax = total_tax + (val1.qty * val1.material_price) * amount / 100
                    self.tax_value = total_tax
    def _get_total_amount(self):
        total_amount = 0.00
        for val in self:
            total_amount = val.amount_untaxed + val.tax_value
            self.total_amount = total_amount

    @api.multi
    def unlink(self):
        if self.state == 'draft':
            return super(JoborderChallanReceipt, self).unlink()
        else:
            if self.state != 'draft' and self.env.user.id == self.env.ref('base.user_admin').id:
                return super(JoborderChallanReceipt, self).unlink()
            else:
                raise ValidationError('You Can not delete a record')

    name = fields.Char('Challan No.', required=True)
    # date = fields.Date('Date', default=fields.Date.today(),required=True,)
    date = fields.Date(required=True, default=lambda self: self._get_current_date())

    @api.model
    def _get_current_date(self):
        """ :return current date """
        return fields.Date.today()
    partner_id = fields.Many2one('my.partner', 'Party Name',required=True,)
    issue_id = fields.Many2one('joborder.challan', 'Issue Challan No.')
    remark = fields.Char('Remark')
    joborder_challan_receipt_lines = fields.One2many('joborder.challan.receipt.line', 'order_id', 'Lines')
    joborder_challan_receipt_lines_rec = fields.One2many('joborder.challan.receipt.line', 'order_id', 'Reconcilation')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('done', 'Lock'),
    ], string='Status', readonly=True, index=True, copy=False, default='draft', )
    amount_untaxed = fields.Float(compute=_amount_all_wrapper, string='Untaxed Amount')
    tax_value = fields.Float(compute=_tax_amount, string='Taxes')
    total_amount = fields.Float(compute=_get_total_amount, string='Total Amount')
    challan_type = fields.Selection([('regular', 'Regular'), ('rework', 'Rework'), ('foc', 'FOC')], default='regular',
                                    string='Challan Type')

    # total_receive = fields.Float(compute=_total_receive, string='Total Receive', store=False)
    # total_issue = fields.Float(compute=_total_issue, string='Total Issue', store=False)
    # total_remaining = fields.Float(compute=_total_remaining, string='Total Remaining', store=False)
    total_rec=fields.Float(string='Tot Rec',digits=(10,2))
    # total_iss = fields.Float(string='Tot Iss', digits=(10, 2))
    total_iss=fields.Float(string='Tot Iss',digits=(10,2),compute="get_total_issue")
    total_bal = fields.Float(string='Bal Qty',digits=(10,2),compute="get_total_issue")
    challan_line_ids = fields.One2many('challan.line', 'challan_reciept_id')
    inspected_ok_qty = fields.Integer('Inspected OK qty',compute="calculate_inspected_ok_qty")
    inspected_rejected_qty = fields.Integer('Inspected Rejected qty',compute="calculate_inspected_rejected_qty")
    inspected_return_ref = fields.Char('Inspection return ref',compute="calculate_inspected_ref")
    production_ok_qty = fields.Integer('Production OK qty',compute="calculated_production_ok_qty")
    production_rework_qty = fields.Integer('Production Rework qty',compute="calculated_production_rework_qty")
    production_notok_qty = fields.Integer('Production Not OK qty',compute="calculated_production_notok_qty")
    inspected_sort_qty = fields.Integer('Inspected Sort qty',compute="calculate_inspected_sort_qty")
    production_return_ref = fields.Char('Production return ref',compute="calculate_production_ref")
    mast_oldid=fields.Integer('Mast ID(sw)')
    gate_entryno=fields.Integer('Gate Entry No')
    gate_entrydate = fields.Date('Gate Entry Date', default=fields.Date.today())
    remark=fields.Char('Remarks')
    inspection_count = fields.Integer('Inspection Count',compute ="action_view_job_order_inspection")
    production_count = fields.Integer('Production Count',compute ="action_view_job_order_production")
    final_inspection_count = fields.Integer('Final Inspection Count',compute ="action_view_job_order_inspection")
    challan_issue_count = fields.Integer('Challan Issue Count',compute ="action_view_job_order_challan_issue")

    def get_total_issue(self):
        for val in self:
            challan_rec = self.env['challan.line'].search([('party_challan','=',val.id),('order_id.partner_id','=',val.partner_id.id)])
            qty = 0.0
            if challan_rec:
                for rec in challan_rec:
                    qty+=rec.qty
            val.total_iss = qty
            val.total_bal = val.total_rec - val.total_iss
            # print(val.total_bal,'===============toyalll')



    def action_view_job_order_challan_issue(self):
        for val in self:
            challan_issue_data = self.env['challan.line'].sudo().read_group(
                [('party_challan', '=', val.id),('order_id.partner_id', '=', val.partner_id.id)], ['id'], ['party_challan'])
            # print(challan_issue_data,'===================challan')
            result = dict((data['party_challan'][0], data['party_challan_count']) for data in challan_issue_data)
            val.challan_issue_count = result.get(self.id, 0)

    def open_challan_issue_history(self):
        action = self.env.ref('job_order_process.action_challan').read()[0]
        action['domain'] = [('partner_id', '=', self.partner_id.id),('challan_line.party_challan', '=', self.id)]
        return action

    def action_view_job_order_inspection(self):
        for val in self:
            inspection_data = self.env['joborder.inspection'].sudo().read_group(
                [('order_ids', '=', val.id),('party_name', '=', val.partner_id.id)], ['id'], ['order_ids'])
            # print(inspection_data,'====================')
            result = dict((data['order_ids'][0], data['order_ids_count']) for data in inspection_data)
            # print(result,'===============result')
            val.inspection_count = result.get(self.id, 0)
            # print(val.inspection_count,'=======================inspection')

    def open_inspection_history(self):
        action = self.env.ref('job_order_process.action_challan_inspection').read()[0]
        action['domain'] = [('order_ids', '=', self.id)]
        return action

    def action_view_job_order_production(self):
        for val in self:
            production_data = self.env['joborder.production'].sudo().read_group(
                [('order_ids', '=', val.id),('party_name', '=', val.partner_id.id)], ['id'], ['order_ids'])
            result = dict((data['order_ids'][0], data['order_ids_count']) for data in production_data)
            # print(result,'===============result')
            val.production_count = result.get(self.id, 0)

    def open_production_history(self):
        action = self.env.ref('job_order_process.action_challan_production').read()[0]
        action['domain'] = [('order_ids', '=', self.id)]
        return action

    def action_view_job_order_final_inspection(self):
        for val in self:
            final_inspection_data = self.env['final.inspection'].sudo().read_group(
                [('order_ids', '=', val.id),('party_name', '=', val.partner_id.id)], ['id'], ['order_ids'])
            result = dict((data['order_ids'][0], data['order_ids_count']) for data in final_inspection_data)
            # print(result,'===============result')
            val.final_inspection_count = result.get(self.id, 0)

    def open_final_inspection_history(self):
        action = self.env.ref('job_order_process.action_final_challan_production').read()[0]
        action['domain'] = [('order_ids', '=', self.id)]
        return action
    # sql_constraints = [
    #     ('name', 'unique(name)', 'Challan no. already exists!')
    # ]
    _sql_constraints = [
        ('name', 'unique(name,partner_id)', 'Challan  no. already exists for this partner!')
    ]





    def calculate_inspected_sort_qty(self):
        qty = 0
        rec = self.env['joborder.inspection'].search([('order_ids.name','=',self.name)])
        for val in rec:
            qty+=val.short_quantity
        self.inspected_sort_qty = qty

    def calculate_inspected_ref(self):
        name = ''
        rec = self.env['joborder.challan'].search([('job_order_challan_reference','=',self.name)])
        for val in rec:
            name+= ',' + val.name
        self.inspected_return_ref = name

    def calculate_production_ref(self):
        name = ''
        rec = self.env['joborder.challan'].search([('production_challan_reference','=',self.name)])
        for val in rec:
            name+= ',' + val.name
        self.production_return_ref = name

    def calculate_inspected_ok_qty(self):
        qty = 0
        rec = self.env['joborder.inspection'].search([('order_ids.name','=',self.name)])
        for val in rec:
            qty+=val.expected_qty
        self.inspected_ok_qty = qty


    def calculate_inspected_rejected_qty(self):
        qty = 0
        rec = self.env['joborder.inspection'].search([('order_ids.name','=',self.name)])
        for val in rec:
            qty+=val.rejected_qty
        self.inspected_rejected_qty = qty

    def calculated_production_ok_qty(self):
        qty = 0
        rec = self.env['final.inspection'].search([('order_ids.name', '=', self.name)])
        for val in rec:
            qty += val.expected_qty
        self.production_ok_qty = qty

    def calculated_production_notok_qty(self):
        qty = 0
        rec = self.env['final.inspection'].search([('order_ids.name', '=', self.name)])
        for val in rec:
            qty += val.rejected_qty
        self.production_notok_qty = qty

    def calculated_production_rework_qty(self):
        qty = 0
        rec = self.env['final.inspection'].search([('order_ids.name', '=', self.name)])
        for val in rec:
            qty += val.rework_qty
        self.production_rework_qty = qty

        # issue_rec = fields.Many2many('challan.line',string="Issue Rec")


class JoborderChallanReceiptLine(models.Model):
    _name = "joborder.challan.receipt.line" #joborder_challan_receipt_line
    _order = 'party_datessss desc'

    def calculate_inspected_ok_qty_line(self):
        # print('============3================',self.id)
        for chalan_id in self:
            qty = 0
            rec = self.env['joborder.inspection'].search([('joborder_challan_receipt_line_id', '=',chalan_id.id)])
            for val in rec:
                qty += val.expected_qty
            chalan_id.inspected_ok_qty_line = qty
    def calculate_inspected_rejected_qty_line(self):
        for line in self:
            qty = 0
            rec=self.env['joborder.inspection'].search([('joborder_challan_receipt_line_id','=',line.id)])
            for val in rec:
                qty += val.rejected_qty
            line.inspected_rejected_qty_line=qty
    # for val in self.env['joborder.challan'].search(
    #         [('partner_id', '=', self.partner_id.id), ('challan_type', '=', 'regular'), ('state', '=', 'confirm')]):
    def calculate_inspected_ref_line(self):
        # name =''
        for line in self:
            rec = self.env['challan.line'].search([('joborder_challan_receipt_line_id','=',line.id)])
            # for val in rec:
            #     name+= ',' + val.name
            line.inspected_return_ref_line = rec.order_id
    def calculated_production_uinsp_qty_line(self):
        for line in self:
            qty = 0
            rec=self.env['final.inspection'].search([('joborder_challan_receipt_line_id','=',line.id)])
            for val in rec:
                qty += val.qty
            line.production_insp_qty_line=qty
    def calculated_production_rem_qty_line(self):
        for line in self:
            qty = 0
            rec=self.env['final.inspection'].search([('joborder_challan_receipt_line_id','=',line.id)])
            for val in rec:
                qty += val.expected_qty
                if val.qty == qty:
                    line.production_rem_qty_line = val.qty - qty
                else:
                    line.production_rem_qty_line = val.qty - qty
                # print('==============rem qty====',qty)
            # print(qty,'================qty',line.expected_qty)
            # qty=line.expected_qty-qty
            # print(qty,'===============qty after')
            # line.production_rem_qty_line=qty
            # print (line.production_rem_qty_line,'=============rem')
    def calculated_production_rework_qty_line(self):
        for line in self:
            qty = 0
            rec=self.env['final.inspection'].search([('joborder_challan_receipt_line_id','=',line.id)])
            for val in rec:
                qty += val.rework_qty
            line.production_rework_qty_line=qty
    def calculated_production_notok_qty_line(self):
        for line in self:
            qty = 0
            rec=self.env['final.inspection'].search([('joborder_challan_receipt_line_id','=',line.id)])
            for val in rec:
                qty += val.rejected_qty
            line.production_notok_qty_line=qty
    def calculated_production_ok_qty_line(self):
        for line in self:
            qty = 0
            rec = self.env['final.inspection'].search([('joborder_challan_receipt_line_id', '=', line.id)])
            for val in rec:
                qty += val.expected_qty
            line.production_ok_qty_line = qty
    def calculated_production_desp_qty_line(self):
        for line in self:
            qty = 0
            rec = self.env['challan.line'].search([('joborder_challan_receipt_line_id', '=', line.id),('order_id.challan_type','=','regular')])
            for val in rec:
                qty += val.qty
            line.production_desp_qty_line = qty
    def calculate_inspected_sort_qty_line(self):
        for line in self:
            qty = 0
            rec=self.env['joborder.inspection'].search([('joborder_challan_receipt_line_id','=',line.id)])
            for val in rec:
                qty += val.short_quantity
            line.inspected_sort_qty_line=qty

    @api.onchange('job_order_id')
    def onchange_job_order(self):
        product_list = []
        data_list = []
        for val in self.env['job.order'].search([('partner_id', '=', self.order_id.partner_id.id),('state','=','confirm')]):
            product_list.append(val.id)
            # print('=====job.order id job order==========', val.id)
        domain = {'job_order_id': [('id', 'in', product_list)]}
        for line in self.env['job.order.line'].search([('order_id', '=', self.job_order_id.id)]):
            data_list.append(line.product_id.id)
        domain.update({'product_id':[('id','in',data_list)]})
        return {'domain': domain}  # ,'domain1':domain1

    @api.depends('job_order_id','partner_id')
    def get_default_joborder_id(self):
        product_list = []
        data_list = []
        for val in self.env['job.order'].search(
                [('partner_id', '=', self.order_id.partner_id.id), ('state', '=', 'confirm')]):
            # print('=====partner_id= hello=========', val.id)
            data_list=data_list.append(val.id)

        # print('=====on change order_id= hello=========', data_list)
        if data_list:
            return data_list[0] # ,'domain1':domain1
    @api.onchange('product_id')
    def onchange_product_id(self):
        # data_rec = self.env['job.order.line'].search(
        #     [('order_id', '=', self.job_order_id.id)])
        # for rec in data_rec:
        #     if self.product_id:
        #         self.unit_id = rec.product_id.unit_id.id
        #         # self.part_id = self.product_id.part_id.id
        #         self.part_no=rec.product_id.part_no
        #         self.sac_code = rec.product_id.category_id.hsn_no
        #         self.hsn_code = rec.product_id.hsn_code
        #         self.tax_id = rec.product_id.sale_tax_id.id
        #         self.process = rec.process_id.id
        #         self.packing_id = rec.packing_id.id
        #         self.per_piece = rec.per_piece
        #         #self.batch_no = self.batch_no
        #         #self.no_of_bin = math.ceil(self.qty/self.per_piece)
        if self.product_id and self.order_id:
            sale_line = self.env['job.order.line'].search(
                [('order_id', '=', self.job_order_id.id), ('product_id', '=', self.product_id.id)])
            self.unit_id = sale_line.product_id.unit_id.id
            # self.part_id = self.product_id.part_id.id
            self.part_no=sale_line.product_id.part_no
            self.sac_code = sale_line.product_id.category_id.hsn_no
            self.hsn_code = sale_line.product_id.hsn_code
            # self.tax_id = sale_line.product_id.sale_tax_id.id
            self.tax_id=sale_line.tax_id
            self.process = sale_line.process_id.id
            self.packing_id = sale_line.packing_id.id
            self.per_piece = sale_line.per_piece
            self.unit_price = sale_line.unit_price
            self.material_price=sale_line.material_price
    # @api.onchange('job_order_id')
    # def onchange_partner_id(self):
    #     product_list = []
    #
    #     if self.order_id.partner_id:
    #         data_list = []
    #         for val in self.env['job.order'].search([('partner_id', '=', self.order_id.partner_id.id)]):
    #             product_list.append(val.id)
    #             for line in self.env['job.order.line'].search([('order_id', '=', val.id)]):
    #                 data_list.append(line.product_id.id)
    #             domain = {'job_order_id': [('id', 'in', product_list)],'product_id': [('id', 'in', data_list)]}
    #         return {'domain': domain} #,'domain1':domain1

    # @api.onchange('part_id')
    # def onchange_part_id(self):
    #     product1 = None
    #     if self.part_id:
    #         product = self.env['my.product'].search([('part_id', '=', self.part_id.id)])
    #
    #         self.unit_id = product.unit_id.id
    #         self.product_id = product.id

    # def get_remaining_qty(self):
    #     res = {}
    #     total_remaining = 0.00
    #
    #     for val in self:
    #         if val.qty:
    #             total_remaining = (val.qty - val.issue_qty)
    #             total_balance = total_remaining
    #             val.write({'qty_remaining': total_remaining})
    #             val.remaining_qty = total_remaining
    #             # val.write({'bal_qtynew':val.remaining_qty})
    #             # val.bal_qtynew = val.remaining_qty
    #             print('bal_qty===========', total_balance,total_remaining)
    #
    #         else:
    #             total_remaining = 0.00
    #             val.remaining_qty = total_remaining
    #     return res
    @api.onchange('qty','per_piece')
    def onchange_qty(self):
        # print('onchange_qty========',self.qty)
        self.bal_qty = self.qty - self.issue_qty
        # res = super(JoborderChallanReceiptLine,self).onchange_qty()
        if self.qty:
            try:
                self.no_of_bin = math.ceil(self.qty / self.per_piece)
            except:
                pass
        if self.per_piece:
            try:
                self.no_of_bin = math.ceil(self.qty / self.per_piece)
            except:
                pass
        # if self.qty and self.issue_qty:
        #     self.bal_qty = self.qty - self.issue_qty
        # return res
    # @api.depends('qty', 'issue_qty')
    # def get_bal_qty(self):
    #
    #
    #
    #     dsafas
    #     # res = super(JoborderChallanReceiptLine, self).get_bal_qty()
    #     self.bal_qty=self.qty-self.issue_qty
    #     sfasffdsdfadf
    #     print('get_bal_qty===========get_bal_qty', self.bal_qty)
    #     # return res
    def get_subtotal(self):
        total_price = 0.00
        for val in self:
            if val.qty:
                total_price = (val.qty * val.material_price)
                val.write({'price_subtotal1': total_price})
                val.price_subtotal = total_price
                val.jw_subtotal=val.qty * val.unit_price
    # @api.onchange('unit_price','product_id')
    # def get_default_material_rate(self):
    #     for val in self:
    #         if val.material_price:
    #             pass
    #         else:
    #             val.material_price=round(val.unit_price*2)
    order_id = fields.Many2one('joborder.challan.receipt', 'Id',ondelete='cascade')
    job_order_id = fields.Many2one('job.order', 'Order No.',default=get_default_joborder_id,required=True,)
    product_id = fields.Many2one('my.product', string='Product',required=True,)
    # part_id = fields.Many2one('part.number', string='Part No', )
    part_no=fields.Char('Part No.')
    unit_id = fields.Many2one('my.unit', 'UOM',required=True,)
    qty = fields.Float('Quantity',digits=(16,2))
    issue_qty = fields.Float('Dispatch Qty',digits=(16,2),readony=True,compute="get_total_balance")
    bal_qtynew=fields.Float('Bal New',digits=(16,2),compute="get_total_balance",store=True)
    # issue_qty = fields.Float('Dispatch Qty', digits=(16, 2), readony=True)
    # bal_qtynew = fields.Float('Bal New', digits=(16, 2))

    # def get_total_balance(self):
    #     for val in self:
    #         challan_rec = self.env['challan.line'].search([('party_challan','=',val.order_id.id),('order_id.partner_id','=',val.order_id.partner_id.id),('product_id','=',val.product_id.id)])
    #         print(challan_rec,'===================line chalan')
    #         print(val.bal_qtynew,val.qty,val.issue_qty,'testing aaaaaaaaaaa')
    #         # val.bal_qtynew =val.qty-val.issue_qty
    #         if not challan_rec:
    #             val.bal_qtynew = val.qty
    #         if challan_rec:  #error corrected
    #             for val1 in challan_rec:
    #                 val.issue_qty +=val1.qty
    #                 val.bal_qtynew -=val1.qty
    def get_total_balance(self):
        for val in self:
            challan_rec = self.env['challan.line'].search(
                [('party_challan', '=', val.order_id.id), ('order_id.partner_id', '=', val.order_id.partner_id.id),
                 ('product_id', '=', val.product_id.id)])
            # print(challan_rec, '===================line chalan')
            if not challan_rec:
                val.bal_qtynew = val.qty
            if challan_rec:
                for line in challan_rec:
                    val.issue_qty += line.qty
                    val.bal_qtynew = val.qty - val.issue_qty

                    # print(val.issue_qty,'val.issue_qty inside for',val.product_id,val.bal_qtynew)
                # print(val.issue_qty, 'val.issue_qty outside for',val.bal_qtynew)
                # val.bal_qtynew = val.qty - val.issue_qty


    unit_price = fields.Float('Unit Rate(Jw)')
    material_price = fields.Float('Rate(Mat)')
    hsn_code = fields.Char('HSN Code')
    sac_code = fields.Char("SAC Code", default='9988')

    # qty_remaining = fields.Float(string='Remaining Qty')

    expected_qty = fields.Float('Accepted Qty',digits=(16,2))
    rejected_qty = fields.Float('Rejected Qty',digits=(16,2))
    osp_qty=fields.Float('OSP Qty',digits=(16,2))
    desp_qty_oldsw=fields.Float('Desp Qty Old Sw',digits=(16,2))
    tax_id = fields.Many2one('my.tax', string='Taxes', )
    price_subtotal = fields.Float(compute=get_subtotal, string='Subtotal')
    price_subtotal1 = fields.Float(string='Subtotal')
    jw_subtotal=fields.Float(compute=get_subtotal, string='Jw Subtotal')
    #related fields starts====================
    party_namesss = fields.Many2one('my.partner', 'Party Name',related="order_id.partner_id")
    party_datessss = fields.Date('Date',related="order_id.date")
    challan_type = fields.Selection([('regular', 'Regular'), ('rework', 'Rework'), ('foc', 'FOC')], default='regular',
                                    string='Challan Type',related="order_id.challan_type")
    # related fields ends====================
    remark = fields.Char('Remark')
    process = fields.Many2one('job.process.master',string="Process")#,required=True,
    packing_id = fields.Many2one('standerd.packing', string="Per Item")
    per_piece = fields.Integer('Std Pking')
    no_of_bin = fields.Integer('NoofBin')
    batch_no = fields.Char('LotNo.')
    inspected_ok_qty_line = fields.Integer('U/prod', compute="calculate_inspected_ok_qty_line")
    inspected_rejected_qty_line = fields.Integer('Insp Rejqty', compute="calculate_inspected_rejected_qty_line")
    # inspected_return_ref_line = fields.Many2one('joborder.challan','Insp Rtnref', compute="calculate_inspected_ref_line")
    inspected_sort_qty_line = fields.Integer('Insp SortQty', compute="calculate_inspected_sort_qty_line")
    production_insp_qty_line = fields.Integer('UF/Insp', compute="calculated_production_uinsp_qty_line")
    production_rem_qty_line = fields.Integer('RemQty', compute="calculated_production_rem_qty_line")

    production_rework_qty_line = fields.Integer('ProdRework', compute="calculated_production_rework_qty_line")
    production_notok_qty_line = fields.Integer('ProdNotOK Qty', compute="calculated_production_notok_qty_line")
    # production_return_ref_line = fields.Char('Production return ref', compute="calculate_production_ref_line")
    production_ok_qty_line = fields.Integer('Desp Ready Qty', compute="calculated_production_ok_qty_line")
    production_desp_qty_line = fields.Integer('Desp Qty', compute="calculated_production_desp_qty_line")

    # rq=fields.Float('RecQty')
    # mq = fields.Float('MoveQty')
    bq = fields.Float('BalQty',digits=(10,2))

    @api.multi
    def unlink(self):
        if self.state == 'draft':
            return super(JoborderChallanReceiptLine, self).unlink()
        else:
            if self.state != 'draft' and self.env.user.id == self.env.ref('base.user_admin').id:
                return super(JoborderChallanReceiptLine, self).unlink()
            else:
                raise ValidationError('You Can not delete a record')



    @api.model
    def create(self,vals):

        vals['batch_no'] = 'INEC' + '/' + datetime.strptime(str(datetime.now().date()), '%Y-%m-%d').strftime(
                    '%d%m%y') + '/' + self.env['ir.sequence'].get('joborder_inspection')
        if vals.get('order_id', False):
            for line in self.env['joborder.challan.receipt'].browse([vals['order_id']]).joborder_challan_receipt_lines:
                if (vals.get('product_id') == line.product_id.id)  and line.id != self.id:
                    raise UserError(_(u"Duplicate lines \nthis line already exist!\ncheck your lines again please!"))
        return super(JoborderChallanReceiptLine,self).create(vals)

    # @api.model
    # def create(self,vals):
    #     vals['batch_no'] = 'NEC' + '/' + datetime.strptime(str(datetime.now().date()), '%Y-%m-%d').strftime(
    #                 '%Y-%m-%d') + '/' + self.env['ir.sequence'].get('joborder_inspection')
    #     if vals.get('order_id', False):
    #         for line in self.env['joborder.challan.receipt'].browse([vals['order_id']]).joborder_challan_receipt_lines:
    #             if (vals.get('product_id') == line.product_id.id)  and line.id != self.id:
    #                 raise UserError(_(u"Duplicate lines \nthis line already exist!\ncheck your lines again please!"))
    #     return super(JoborderChallanReceiptLine,self).create(vals)

    @api.multi
    def write(self, vals):
        for rec in self:
            if 'product_id' in vals:
                prod = self.env['my.product'].browse([vals.get('product_id')])
            else:
                prod = rec.product_id

            # if 'party_challan' in vals:
            #     challan = self.env['joborder.challan.receipt'].browse([vals.get('party_challan')])
            # else:
            #     challan = rec.party_challan
            for line in self.env['joborder.challan.receipt'].browse([rec.order_id.id]).joborder_challan_receipt_lines:
                if (prod.id == line.product_id.id)  and line.id != rec.id:#and (challan.id == line.party_challan.id)
                    raise UserError(
                        _(u"Duplicate lines \n This line already exist!\n Check your lines again please!"))
        result = super(JoborderChallanReceiptLine, self).write(vals)
        return result
# class JoborderChallanReceiptIssueLine(models.Model):
#     _name = 'challan.liner'
#     _order = 'party_challan,product_id'
#
#     order_id = fields.Many2one('joborder.challan','Id',ondelete='cascade')
#     job_order_id = fields.Many2one('job.order', 'Order No.')
#
#     party_challan =fields.Many2one('joborder.challan.receipt', 'Party Challan', ondelete='cascade')
#     product_id = fields.Many2one('my.product','Product')
#     name = fields.Char('Description',default='For Platting')
#     # part_id = fields.Many2one('part.number','Part No.')
#     part_no=fields.Char('Part No.')
#     hsn_code = fields.Char('HSN No.')
#     # unit_id = fields.Many2one('my.uom','UOM')
#     unit_id = fields.Many2one('my.unit', 'UOM')
#     qty = fields.Float('Quantity')
#
#     qty_nos=fields.Integer('Qty Nos')
#     qty_kg=fields.Float('Qty_Kg')
#     unit_price = fields.Float('Unit Price')
#     material_price = fields.Float('Material Price')
#
#     nature_of_process = fields.Char('Nature of Process')
#
#     tax_id = fields.Many2one('my.tax', string='Taxes',)
#     price_subtotal = fields.Float(string='Subtotal')
#     challan_issue_id=fields.Char(string='Issue ChNo')
#     # joborder_challan_receipt_line_id=fields.Integer()
#     joborder_challan_receipt_line_id= fields.Many2one('joborder.challan.receipt.line', ondelete='cascade')
#     bq = fields.Float('Bal qty')
#     rtq = fields.Float('Return qty')



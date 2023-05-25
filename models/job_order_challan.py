from odoo import api, fields, models,_
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class JoborderChallan(models.Model):
    _name="joborder.challan"
    _order = 'id desc'

    @api.multi
    # def unlink(self):
    #     if self.env.user.id == self.env.ref('base.user_admin').id:
    #         return super(JoborderChallan, self).unlink()
    #     else:
    #         raise ValidationError('You Can not delete a record')
    # @api.multi
    def unlink(self):
        if self.state == 'draft':
            return super(JoborderChallan, self).unlink()
        else:
            if self.state != 'draft' and self.env.user.id == self.env.ref('base.user_admin').id:
                return super(JoborderChallan, self).unlink()
            else:
                raise ValidationError('You Can not delete a record')



    @api.model
    def create(self, vals):
        challan_rec = self.env['joborder.challan'].search([('name', '=', vals['name'])])
        if challan_rec:
            raise ValidationError('Challan No Already Exist!')
        total_qty = 0
        total = 0
        seq=''
        a=''
        if vals['challan_type'] == 'regular':
            a = ''
            seq = self.env['ir.sequence'].get('job_order_challan')
        if vals['challan_type'] == 'rework':
            a = 'Rw-'
            seq = self.env['ir.sequence'].get('job_order_challan1')
        if vals['challan_type'] == 'foc':
            # a = 'Foc-'
            seq = self.env['ir.sequence'].get('job_order_challan')
        if vals['challan_type'] == 'return':
            a = 'Ret-'
            seq = self.env['ir.sequence'].get('job_order_challan3')
        if vals['challan_type'] == 'osp':
            a = 'osp-'
            seq = self.env['ir.sequence'].get('job_order_challan4')

        # vals['name']=a

        vals['name'] = a + str(seq)
        sum_id = super(JoborderChallan, self).create(vals)
        return sum_id

    def action_create_bill(self):
        data = []
        if self.challan_type not in ['foc','rework']:
            bill_rec = self.env['challan.bill']
            for line in self.challan_line:
                job_rec = self.env['job.order.line'].search([('order_id','=',line.job_order_id.id),('product_id','=',line.product_id.id)])
                # if job_rec.unit_price == 0:
                #     raise ValidationError('Bill Not Generated Autometically')
                # else:
                data.append((0,0,{
                    'party_challan':line.party_challan.id,
                    'product_id':line.product_id.id,
                    # 'part_id':line.part_id.id,
                    'part_no':line.part_no,
                    'sac_code':line.product_id.category_id.hsn_no,
                    'our_challan':self.id,
                    # val1.product_id.category_id.hsn_no
                    'qty':line.qty,
                    'unit_id':line.unit_id.id,
                    'unit_price': job_rec.unit_price,
                    # 'unit_price':line.party_challan.unit_price,
                    'tax_id':[(4,tax.id) for tax in job_rec.tax_id],
                    'price_subtotal':line.price_subtotal,
                    'qty_nos': int(line.qty) if ((line.unit_id.name.lower())[0] == 'n') else 0,
                    'qty_kg': line.qty if ((line.unit_id.name.lower())[0] != 'n') else 0,
                    'bq':line.bq
                }))
                line.bq = line.bq - line.qty
            bill_rec.create({
                'job_order_id':self.get_challna_line_po(),
                'job_order_date':self.get_challna_line_podate(),
                'vehicle_no':self.vehicle_no.id,
                'payment_term_ids':self.payment_term_recs,
                'partner_id':self.partner_id.id,
                'challan_bill_line':data,
                'challan_issue':[(6,0,[line.order_id.id])]})
            self.billed = True

    def _amount_all_wrapper(self):
        total_amount = 0.00
        for val in self:
            if val.challan_line:
                for val1 in val.challan_line:
                    total_amount = total_amount + val1.amount
                    self.amount_untaxed = total_amount

    def _tax_amount(self):
        total_tax = 0.00
        for val in self:
            if val.challan_line:
                for val1 in val.challan_line:
                    amount = 0.0
                    for val2 in val1.tax_id.children_tax_ids:
                        amount = amount + val2.amount
                    total_tax = total_tax + (val1.qty * val1.material_price)* amount / 100
                    self.tax_value = total_tax

    def _get_total_amount(self):
        total_amount = 0.00
        for val in self:
            total_amount = val.amount_untaxed + val.tax_value
            self.total_amount = total_amount

    @api.multi
    def action_fetch_receipt_data(self):
        if self.challan_line:
            for line in self.challan_line:
                line.unlink()
        data = []
        if self.challan_type == 'regular':
            final_inspection_rec = self.env['final.inspection'].search([('party_name', '=', self.partner_id.id),('is_issue','=',False),('expected_qty','>',0)])
            for rec in final_inspection_rec:
                job_rec = self.env['joborder.challan.receipt.line'].search(
                    [('order_id', '=', rec.order_ids.id), ('product_id', '=', rec.product_id.id)])
                job_work_rec = self.env['job.order.line'].search([('product_id','=',rec.product_id.id),('order_id','=',job_rec.job_order_id.id)])
                if rec.expected_qty > 0:
                    data = [(0, 0, {
                        'product_id': rec.product_id.id,
                        'name': rec.product_id.name,
                        'hsn_code': rec.product_id.hsn_code,
                        'party_challan': rec.order_ids.id,
                        'qty': rec.expected_qty,
                        'batch_no':rec.batch_no,
                        # 'part_id': line.part_id.id,
                        'part_no': rec.part_no,
                        'unit_id': rec.unit_id.id,
                        'job_order_id': job_rec.job_order_id.id,
                        'unit_price': job_work_rec.unit_price,
                        'material_price': job_work_rec.material_price,
                        'tax_id': job_work_rec.tax_id.id,
                        'joborder_challan_receipt_line_id': job_rec.id,
                        'qty_nos': int(rec.expected_qty) if ((rec.unit_id.name.lower())[0] == 'n') else 0,
                        'qty_kg': rec.expected_qty if ((rec.unit_id.name.lower())[0] != 'n') else 0,
                        # 'bq': qty
                    })]
                    self.challan_line = data


            # receipt_rec = self.env['joborder.challan.receipt'].search([('partner_id','=',self.partner_id.id)])
            # #final_inspection_rec = self.env['final.inspection'].search([('is_issue','=',False)])
            # for rec in receipt_rec:
            #     if rec.joborder_challan_receipt_lines_rec:
            #         for line in rec.joborder_challan_receipt_lines_rec:
            #             self.payment_term_recs =line.job_order_id.payment_term
            #             qty = line.production_ok_qty_line - line.production_desp_qty_line
            #             if qty > 0:
            #                 data=[(0,0,{
            #                     'product_id': line.product_id.id,
            #                     'name':line.product_id.name,
            #                     'hsn_code':line.product_id.hsn_code,
            #                     'party_challan': rec.id,
            #                     'qty': qty,
            #                     # 'part_id': line.part_id.id,
            #                     'part_no':line.part_no,
            #                     'unit_id': line.unit_id.id,
            #                     'job_order_id': line.job_order_id.id,
            #                     'unit_price': line.unit_price,
            #                     'material_price': line.material_price,
            #                     'tax_id': line.tax_id.id,
            #                     'joborder_challan_receipt_line_id':line.id,
            #                     'qty_nos':int(qty) if ((line.unit_id.name.lower())[0] =='n') else 0,
            #                     'qty_kg':qty if ((line.unit_id.name.lower())[0] !='n') else 0,
            #                     #'bq': qty
            #                 })]

        elif self.challan_type == 'return':

            inspection_rec = self.env['joborder.inspection'].search([('party_name', '=', self.partner_id.id),('is_return','=',False)])
            for rec in inspection_rec:
                job_rec = self.env['joborder.challan.receipt.line'].search([('order_id','=',rec.order_ids.id),('product_id','=',rec.product_id.id)])
                if rec.rejected_qty > 0:
                    data = [(0, 0, {
                        'product_id': rec.product_id.id,
                        'name': rec.product_id.name,
                        'hsn_code': rec.product_id.hsn_code,
                        'party_challan': rec.order_ids.id,
                        'qty': rec.rejected_qty,
                        # 'part_id': line.part_id.id,
                        'part_no': rec.part_no,
                        'unit_id': rec.unit_id.id,
                        'job_order_id': job_rec.job_order_id.id,
                        'unit_price': job_rec.unit_price,
                        'material_price': job_rec.material_price,
                        'tax_id': job_rec.tax_id.id,
                        'joborder_challan_receipt_line_id': job_rec.id,
                        'qty_nos': int(rec.rejected_qty) if ((rec.unit_id.name.lower())[0] == 'n') else 0,
                        'qty_kg': rec.rejected_qty if ((rec.unit_id.name.lower())[0] != 'n') else 0,
                        # 'bq': qty
                    })]
                    self.challan_line = data
            # final_inspection_rec = self.env['final.inspection'].search([('party_name', '=', self.partner_id.id),('is_return','=',False)])
            # for rec in final_inspection_rec:
            #     job_rec = self.env['joborder.challan.receipt.line'].search([('order_id','=',rec.order_ids.id),('product_id','=',rec.product_id.id)])
            #     if rec.rejected_qty > 0:
            #         data.append({
            #             'product_id': rec.product_id.id,
            #             'name': rec.product_id.name,
            #             'hsn_code': rec.product_id.hsn_code,
            #             'party_challan': rec.order_ids.id,
            #             'qty': rec.rejected_qty,
            #             # 'part_id': line.part_id.id,
            #             'part_no': rec.part_no,
            #             'unit_id': rec.unit_id.id,
            #             'job_order_id': job_rec.job_order_id.id,
            #             'unit_price': job_rec.unit_price,
            #             'material_price': job_rec.material_price,
            #             'tax_id': job_rec.tax_id.id,
            #             'joborder_challan_receipt_line_id': job_rec.id,
            #             'qty_nos': int(rec.rejected_qty) if ((rec.unit_id.name.lower())[0] == 'n') else 0,
            #             'qty_kg': rec.rejected_qty if ((rec.unit_id.name.lower())[0] != 'n') else 0,
            #             # 'bq': qty
            #         })
            # self.challan_line = data

    def get_time(self):
        date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        date_time = datetime.strptime(date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5, minutes=30, seconds=0)
        date_time  = date_time .strftime('%H:%M')
        return date_time

    def _amount_all_wrapper(self):
        total_amount = 0.00
        for val in self:
            if val.challan_line:
                for val1 in val.challan_line:
                    total_amount = total_amount + val1.price_subtotal
                    self.amount_untaxed = total_amount

    def _tax_amount(self):
        total_tax = 0.00
        for val in self:
            if val.challan_line:
                for val1 in val.challan_line:
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

    def action_fetch_data(self):
        if self.ref_challan and not self.challan_line:
            for val in self.ref_challan:
                for val1 in val.joborder_challan_receipt_lines:
                    self.env['challan.line'].create(
                        {'order_id': self.id,
                         'party_challan':val.id,
                         'product_id':val1.product_id.id,
                         # 'part_id':val1.part_id.id,
                         'part_no':val1.part_no,
                         'unit_id': val1.unit_id.id,
                         'hsn_code': val1.hsn_code,
                         'qty': val1.qty,
                         'unit_price': val1.unit_price,
                         'material_price': val1.material_price,
                         'tax_id': val1.tax_id.id,
                         })

    def action_confirm(self):
        if self.chno:
            self.name = self.chno

        for val1 in self.challan_line:
            val1.qty_nos = val1.qty if (val1.unit_id.name.lower())[0] == 'n' else 0
            val1.qty_kg = val1.qty if (val1.unit_id.name.lower())[0] != 'n' else 0
            inspection_rec = self.env['joborder.inspection'].search([('product_id','=',val1.product_id.id),('order_ids','=',val1.party_challan.id)])
            for insp in inspection_rec:
                insp.is_return=True
                insp.bq -= insp.rejected_qty

            val1.bq = val1.qty
            final_inspection_rec = self.env['final.inspection'].search(
                [('product_id','=',val1.product_id.id),('order_ids','=',val1.party_challan.id)])
            for final_rec in final_inspection_rec:
                final_rec.bq = val1.bq - final_rec.bq
                final_rec.is_issue = True
                if final_rec.bq == 0:
                    final_rec.state = 'confirm'
            sale_line_obj = self.env['joborder.challan.receipt.line'].search(
                [('product_id', '=', val1.product_id.id), ('unit_id', '=', val1.unit_id.id),
                 ('order_id', '=', val1.party_challan.id)])
            for data in sale_line_obj:
                # sale_line_obj.write({'issue_qty': data.issue_qty + val1.qty,
                #                      'bal_qtynew': data.bal_qtynew - val1.qty,
                #                      })
                sale_line_obj.write({'issue_qty': data.issue_qty + val1.qty,
                                     'bal_qtynew': (data.qty-data.issue_qty),
                                     })

                # rec_obj.write({'remaining_total': rec_obj.remaining_total - val1.qty})
        for rec in self.challan_line:

            rec.joborder_challan_receipt_line_id = sale_line_obj.id
            rec.party_challan.challan_line_ids = [(0, sale_line_obj.id, dict(
                # order_id=rec.order_id.id,
                challan_issue_id=rec.order_id.name,
                product_id=rec.product_id.id,
                unit_price=rec.unit_price,
                name=rec.name,
                tax_id=rec.tax_id.id,
                party_challan=rec.party_challan.id,
                qty=rec.qty,
                product_id1=rec.product_id1.id,
                unit_id=rec.unit_id.id,
                hsn_code=rec.hsn_code,
                # part_id=rec.part_id.id,
                part_no=rec.part_no,
                challan_reciept_id=rec.party_challan.id,
                job_order_id = rec.job_order_id.id

            ))]
        if self.partner_id.billing_mode:
            self.action_create_bill()
        # self.method_update_challan_receipt_total_iss(self.challan_line)
        self.write({'state':'confirm'})

    # def method_update_challan_receipt_total_iss(self,challanline):
    #     for lines in challanline:
    #         rec_obj = self.env['joborder.challan.receipt'].search(
    #             [('id', '=', lines.party_challan.id)])
    #
    #         rec_obj.total_iss+=lines.qty
    #         rec_obj.total_bal-=lines.qty

    # Change By Ayush
    def action_gen_invoice(self):
        action = self.env.ref('job_order_process.action_challan_bill').read()[0]
        action['domain'] = [('partner_id', '=', self.partner_id.id), ('challan_issue', '=',self.id)]
        return action

    name = fields.Char('Issue No.', required=True,default='New')
    chno = fields.Char('Issue No.Org')
    partner_id = fields.Many2one('my.partner','Party Name',required=True,)
    # date = fields.Date('Date',default=fields.Date.today(),required=True,)
    date = fields.Date(required=True, default=lambda self: self._get_current_date())
    @api.model
    def _get_current_date(self):
        """ :return current date """
        date = datetime.now() + timedelta(hours=5, minutes=30)
        date = date.date()
        return date

    remark = fields.Char('Remark')
    origin = fields.Many2one('joborder.challan.receipt', 'Refecence')
    reference_id = fields.Many2many('joborder.challan.receipt', 'Refecence')
    ref_challan = fields.Many2many('joborder.challan.receipt', string='Reference')
    challan_line = fields.One2many('challan.line','order_id','Lines')
    user_id = fields.Many2one('res.users', 'Created By', default=lambda self: self.env.user)
    amount_untaxed = fields.Float(compute = _amount_all_wrapper, string='Untaxed Amount' )
    tax_value = fields.Float(compute = _tax_amount, string='Taxes' )
    total_amount = fields.Float(compute = _get_total_amount, string='Total Amount')
    # eway_bill = fields.Char('E-way Bill No.')
    # transport = fields.Char('Transport Mode')
    vehicle_no = fields.Many2one('vehicle', 'Vehicle No')
    time = fields.Char('Time',default=get_time)
    amount_untaxed = fields.Float(compute=_amount_all_wrapper, string='Untaxed Amount')
    tax_value = fields.Float(compute=_tax_amount, string='Taxes')
    total_amount = fields.Float(compute=_get_total_amount, string='Total Amount')
    challan_type = fields.Selection([('regular', 'Regular'),('rework', 'Rework'),('foc', 'FOC'),('return','Return'),('osp','Returnable Challan')],default='regular',string='Challan Type',required=True)
    billed = fields.Boolean('Billed')
    description = fields.Char('Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
    ], string='Status', readonly=True, copy=False, index=True, default='draft')
    payment_term_recs = fields.Integer(string="Payment term (days)")
    job_order_challan_reference = fields.Char('Reference')
    production_challan_reference = fields.Char('Pro Reference')
    mast_oldid = fields.Integer('Mast Id')

    _sql_constraints = [
        ('name', 'unique(name,partner_id)', 'Challan  no. already exists for this party!')
    ]



#new changes ayush gupta
    def get_challna_line_po(self):
        data = []
        data_line = []
        for line in self.challan_line:
            if data_line:
                # data_line.append(line.job_order_id.name + ' dt.' + datetime.strptime(str(line.job_order_id.date),'%Y-%m-%d').strftime('%d/%m/%Y'))
                data_line.append(line.job_order_id.name)
                # podate=line.job_order_id.date
            else:
                data_line.append(line.job_order_id.name)
            #     data_line.append(line.job_order_id.name + ' dt.' + datetime.strptime(str(line.job_order_id.date),'%Y-%m-%d').strftime('%d/%m/%Y'))
            #
        data_line=set(data_line)

        s = [str(i) for i in data_line]
        res = str(",".join(set(s)))
        return res

    def get_challna_line_podate(self):
        data = []
        data_line = []
        for line in self.challan_line:
            if data_line:
                # data_line.append(line.job_order_id.name + ' dt.' + datetime.strptime(str(line.job_order_id.date),'%Y-%m-%d').strftime('%d/%m/%Y'))
                data_line.append(datetime.strptime(str(line.job_order_id.date),'%Y-%m-%d').strftime('%d/%m/%y'))
                # podate=line.job_order_id.date
            else:
                data_line.append(datetime.strptime(str(line.job_order_id.date),'%Y-%m-%d').strftime('%d/%m/%y'))
            #     data_line.append(line.job_order_id.name + ' dt.' + datetime.strptime(str(line.job_order_id.date),'%Y-%m-%d').strftime('%d/%m/%Y'))
            #
        data_line = set(data_line)
        s = [str(i) for i in data_line]
        res = str(",".join(set(s)))
        return res

    def get_receiptChallanNo(self, ReceiptChallanNO):
        if ReceiptChallanNO:
            return  ReceiptChallanNO.split('_')[0]

class ChallanLine(models.Model):
    _name = "challan.line"

    # @api.multi
    # def unlink(self):
    #     if self.env.user.id == self.env.ref('base.user_admin').id:
    #         return super(ChallanLine, self).unlink()
    #         # self.env[joborder.challan.receipt.line].get_total_balance()
    #         # print(data.qty, data.issue_qty, val1.qty, 'eeeeeeeee', (data.qty - data.issue_qty))
    #     else:
    #         raise ValidationError('You Can not delete a record')
    # @api.multi
    # def unlink(self):
    #     if self.state == 'draft':
    #         return super(ChallanLine, self).unlink()
    #     else:
    #         if self.state != 'draft' and self.env.user.id == self.env.ref('base.user_admin').id:
    #             return super(ChallanLine, self).unlink()
    #         else:
    #             raise ValidationError('You Can not delete a record')
    @api.multi
    def write(self, vals):
        for rec in self:
            if 'product_id' in vals:
                prod = self.env['my.product'].browse([vals.get('product_id')])
            else:
                prod = rec.product_id

            if 'party_challan' in vals:
                challan = self.env['joborder.challan.receipt'].browse([vals.get('party_challan')])
            else:
                challan = rec.party_challan

            for line in self.env['joborder.challan'].browse([rec.order_id.id]).challan_line:
                if (prod.id == line.product_id.id) and (challan.id == line.party_challan.id) and line.id != rec.id and line.order_id == rec.id:
                    raise UserError(_(u"Duplicate lines \nthis line already exist!\ncheck your lines again please!"))
        result = super(ChallanLine, self).write(vals)
        return result

    @api.model
    def create(self, vals):
        if vals.get('order_id', False):
            for line in self.env['joborder.challan'].browse([vals['order_id']]).challan_line:
                if (vals.get('product_id') == line.product_id.id) and (vals.get('party_challan') == line.party_challan.id):
                    raise UserError(_(u"Duplicate lines \nthis line already exist!\ncheck your lines again please!"))
        result = super(ChallanLine, self).create(vals)
        return result

    @api.onchange('job_order_id')
    def onchange_job_order_product(self):
        product_list = []
        job = []
        for val in self.env['job.order'].search([('partner_id', '=', self.order_id.partner_id.id),('state','=','confirm')]):
            job.append(val.id)
        domain = {'job_order_id':[('id','in',job)]}
        for line in self.env['joborder.challan.receipt.line'].search([('job_order_id', '=', self.job_order_id.id),('bal_qtynew','>',0)]):
            product_list.append(line.product_id.id)
        product_list = list(set(product_list))
        domain.update({'product_id': [('id', 'in', product_list)]})
        return {'domain': domain}  # ,'domain1':d

    # @api.onchange('product_id')
    # def onchange_product_id(self):
    #     product_list = []
    #     data_list = []
    #     if self.product_id:
    #         for val in self.env['joborder.challan.receipt.line'].search([('product_id', '=', self.product_id.id),('bal_qtynew','>',0)]):
    #             data_list.append(val.order_id.id)
    #         domain = {'party_challan': [('id', 'in', data_list)]}
    #
    #                 # self.process = rec.process_id.id
    #                 # self.packing_id = rec.packing_id.id
    #         return {'domain': domain}
    @api.onchange('product_id')
    def onchange_product_id(self):
        product_list = []
        data_list = []
        if self.product_id:
            for val in self.env['joborder.challan.receipt.line'].search(
                    [('product_id', '=', self.product_id.id), ('bal_qtynew', '>', 0),
                     ('order_id.partner_id', '=', self.order_id.partner_id.id),
                     ('order_id.challan_type', '=', self.order_id.challan_type)]):
                data_list.append(val.order_id.id)
            domain = {'party_challan': [('id', 'in', data_list)]}

            # self.process = rec.process_id.id
            # self.packing_id = rec.packing_id.id
            self.hsn_code=self.product_id.hsn_code
            job_rec = self.env['job.order.line'].search(
                [('order_id', '=', self.job_order_id.id), ('product_id', '=', self.product_id.id)])
            for val in job_rec:
                self.material_price=val.material_price

            return {'domain': domain}

    @api.onchange('party_challan')
    def get_product_detail(self):
        for val in self.env['joborder.challan.receipt.line'].search([('order_id', '=', self.party_challan.id)]):
            for line in val:
                if val.product_id.id == self.product_id.id:
                    if self.product_id:
                        self.unit_id = line.unit_id.id
                        # self.part_id = line.part_id.id
                        self.part_no = line.product_id.part_no if line.product_id.part_no else '',
                        # self.job_order_id = line.job_order_id.id
                        self.sac_code = line.sac_code
                        self.hsn_code = self.product_id.hsn_code
                        self.tax_id = line.tax_id.id
                        self.unit_price = line.unit_price
                        # self.material_price = self.material_price
                        self.qty = line.bal_qtynew


    @api.onchange('qty')
    def change_qty(self):
        if self.qty:
            for val in self.env['joborder.challan.receipt.line'].search([('order_id', '=', self.party_challan.id),('product_id','=',self.product_id.id)]):
                if val.product_id.id == self.product_id.id:
                    if round(self.qty,2) > val.bal_qtynew:
                        raise ValidationError('Qty is not more than %s'%val.bal_qtynew)



    @api.depends('qty','unit_price')
    def get_subtotal(self):
        total_price = 0.00
        for val in self:
            if val.qty:
                total_price = (val.qty * val.material_price)
                val.write({'price_subtotal1': total_price})
                val.price_subtotal = total_price



    order_id = fields.Many2one('joborder.challan','Id',ondelete='cascade')
    job_order_id = fields.Many2one('job.order', 'Order No.',required=True)

    party_challan =fields.Many2one('joborder.challan.receipt', 'Party Challan', ondelete='cascade')
    challan_reciept_id = fields.Many2one('joborder.challan.receipt', 'Party Challan id', ondelete='cascade')

    product_id = fields.Many2one('my.product','Product',required=True)
    product_id1 = fields.Many2one('my.vik', 'Item')
    name = fields.Char('Description',default='After Platting')
    # part_id = fields.Many2one('part.number','Part No.')
    part_no=fields.Char('Part No.')
    hsn_code = fields.Char('HSN No.')
    # unit_id = fields.Many2one('my.uom','UOM')
    unit_id = fields.Many2one('my.unit', 'UOM')
    qty = fields.Float('Quantity',digits=(10,2))

    qty_nos=fields.Integer('Qty Nos')
    qty_kg=fields.Float('Qty_Kg',digits=(10,2))
    unit_price = fields.Float('Unit Price')
    material_price = fields.Float('Material Price')

    nature_of_process = fields.Char('Nature of Process')

    tax_id = fields.Many2one('my.tax', string='Taxes',)
    price_subtotal = fields.Float(compute=get_subtotal, string='Subtotal')
    price_subtotal1 = fields.Float(string='Subtotal')
    challan_issue_id=fields.Char(string='Issue ChNo')
    # joborder_challan_receipt_line_id=fields.Integer()
    joborder_challan_receipt_line_id= fields.Many2one('joborder.challan.receipt.line', ondelete='cascade')
    bq = fields.Float('Bal qty')
    rtq = fields.Float('Return qty')
    batch_no=fields.Char('Batch No')

class MyVik(models.Model):
    _name = "my.vik"
    _order = 'name asc'

    name = fields.Char('Name')
    product_id = fields.Many2one('my.product', 'Product')
    challan_id = fields.Many2one('joborder.challan.receipt','Challan')
    qty = fields.Float('Qty')

    @api.multi
    def unlink(self):
        if self.env.user.id == self.env.ref('base.user_admin').id:
            return super(MyVik, self).unlink()
        else:
            raise ValidationError('You Can not delete a record')

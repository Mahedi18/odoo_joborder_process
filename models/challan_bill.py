from odoo import api, fields, models
from datetime import datetime, timedelta
import num2words
from odoo.exceptions import UserError, ValidationError


class ChallanBill(models.Model):
    _name = "challan.bill"
    _order = 'id desc'

    # @api.multi
    # def unlink(self):
    #     if self.env.user.id == self.env.ref('base.user_admin').id:
    #         return super(ChallanBill, self).unlink()
    #     else:
    #         raise ValidationError('You Can not delete a record')



    @api.multi
    def unlink(self):
        if self.state == 'draft':
            return super(ChallanBill, self).unlink()
        else:
            if self.state != 'draft' and self.env.user.id == self.env.ref('base.user_admin').id:
                return super(ChallanBill, self).unlink()
            else:
                raise ValidationError('You Can not delete a record')




    @api.model
    def create(self, vals):

        seq = self.env['ir.sequence'].get('challan_bill')
        vals['name'] = '' + str(seq)
        sum_id = super(ChallanBill, self).create(vals)
        return sum_id

    def _tax_amount(self):
        for val in self:
            total_tax = 0.00
            if val.challan_line:
                for val1 in val.challan_line:
                    amount = 0.0
                    for val2 in val1.tax_id.children_tax_ids:
                        amount = amount + val2.amount
                    total_tax = total_tax + (val1.qty * val1.unit_price) * amount / 100
                    self.tax_value = total_tax

    def _get_total_amount(self):
        for val in self:
            total_amount = 0.00
            total_amount = val.amount_untaxed + val.tax_value
            val.total_amount = total_amount
            val.round_amount = round(val.total_amount) - val.total_amount
            val.total_amount = val.total_amount +  val.round_amount

    @api.multi
    def _compute_cgst_total(self):
        for vall in self:
            if vall.challan_bill_line:
                cgst_total = 0.0
                igst_total = 0.0
                sgst_total = 0.0
                for val in vall.challan_bill_line:
                    cgst_total = cgst_total + val.qty * val.unit_price * val.tax_id.amt / 100
                    sgst_total = cgst_total + val.qty * val.unit_price * val.tax_id.amt / 100
                    igst_total = igst_total + val.qty * val.unit_price * val.tax_id.amt / 100
                if vall.user_id.company_id.state_id == vall.partner_id.state_id:
                    vall.cgst_total = round(cgst_total / 2, 2)
                    vall.sgst_total = round(cgst_total / 2, 2)
                    vall.igst_total = 0.0
                else:
                    vall.igst_total = igst_total
                    vall.cgst_total = 0.0
                    vall.sgst_total = 0.0

    def get_receiptChallanNo(self, ReceiptChallanNO):
        if ReceiptChallanNO:
            return ReceiptChallanNO.split('_')[0]

    def _amount_all_wrapper(self):
        for val in self:
            total_amount = 0.00
            if val.challan_bill_line:
                for val1 in val.challan_bill_line:
                    total_amount = total_amount + val1.price_subtotal
                    val.amount_untaxed = total_amount

    def _tax_amount(self):
        for val in self:
            total_tax = 0.00
            if val.challan_bill_line:
                for val1 in val.challan_bill_line:
                    amount = 0.0
                    if val1.tax_id:
                        amount = amount + val1.tax_id.amt

                    total_tax = total_tax + (val1.qty * val1.unit_price) * amount / 100
                    val.tax_value = total_tax

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        domain = {}
        partner_list = []
        if self.partner_id:
            for val in self.env['joborder.challan'].search(
                    [('partner_id', '=', self.partner_id.id), ('challan_type', '=', 'regular'),
                     ('state', '=', 'confirm'), ('billed', '=', False)]):
                partner_list.append(val.id)
            self.challan_issue = [(6, 0, partner_list)]
            domain = {'challan_issue': [('id', '=', partner_list)]}
        return {'domain': domain}

    def action_confirm(self):
        for data in self.challan_bill_line:
            data.bq = data.bq - data.qty
        if self.challan_issue:
            for val in self.challan_issue:
                val.write({'billed': True})

        self.write({'state': 'confirm'})
    # def get_challna_line_po(self):
    #     print('=====get_challna_line_po==========')
    #     data = []
    #     data_line = []
    #     for line in self.challan_line:
    #         if data_line:
    #             # data_line.append(line.job_order_id.name + ' dt.' + datetime.strptime(str(line.job_order_id.date),'%Y-%m-%d').strftime('%d/%m/%Y'))
    #             data_line.append(line.job_order_id.name)
    #             # podate=line.job_order_id.date
    #         else:
    #             data_line.append(line.job_order_id.name)
    #         #     data_line.append(line.job_order_id.name + ' dt.' + datetime.strptime(str(line.job_order_id.date),'%Y-%m-%d').strftime('%d/%m/%Y'))
    #         #
    #     data_line=set(data_line)
    #
    #     s = [str(i) for i in data_line]
    #     res = str(",".join(set(s)))
    #     return res

    def action_fetch_data(self):
        polst=[]
        c=0
        if self.challan_issue:
            if self.challan_bill_line:
                for line in self.challan_bill_line:
                    line.unlink()

            for val in self.challan_issue:
                c += 1
                for val1 in val.challan_line:

                    job_rec_line = self.env['job.order.line'].search(
                        [('order_id', '=', val1.job_order_id.id), ('product_id', '=', val1.product_id.id)])
                    # print(val1.job_order_id.name,'========',type(val1.job_order_id.name),type(val1.job_order_id.date))
                    self.job_order_id=val1.job_order_id.name
                    self.job_order_date=val1.job_order_id.date.strftime("%d/%m/%Y")

                    self.env['challan.bill.line'].create({
                        'order_id': self.id,
                        'party_challan': val1.party_challan.id,
                        'our_challan': val1.order_id.id,
                        'product_id': val1.product_id.id,
                        # 'part_id': val1.part_id.id,
                        'Part_no': val1.part_no,
                        'unit_id': val1.unit_id.id,
                        'sac_code': val1.product_id.category_id.hsn_no,
                        'qty': val1.qty,
                        'qty_nos': int(val1.qty) if ((val1.unit_id.name.lower())[0] == 'n') else 0,
                        'qty_kg': val1.qty if ((val1.unit_id.name.lower())[0] != 'n') else 0,
                        # 'unit_price': val1.job_order_id.unit_price,
                        'unit_price': job_rec_line.unit_price,
                        'tax_id': [(6, 0, [job_rec_line.tax_id.id])], })
        # polst=set(polst)
        # for po in polst:
        #     self.job_order_id +=po
        if c == 1:
            # print('=======c===', c, val.vehicle_no)
            self.vehicle_no = val.vehicle_no

        if not self.challan_issue:
            if self.challan_bill_line:
                for line in self.challan_bill_line:
                    line.unlink()
            challan = self.env['joborder.challan'].search(
                [('partner_id', '=', self.partner_id.id), ('challan_type', '=', 'regular'), ('billed', '=', False),
                 ('state', '=', 'confirm')])
            for val in challan:
                for val1 in val.challan_line:
                    job_rec_line = self.env['job.order.line'].search(
                        [('order_id', '=', val1.job_order_id.id), ('product_id', '=', val1.product_id.id)])
                    self.env['challan.bill.line'].create(
                        {'order_id': self.id,
                         'party_challan': val1.party_challan.id,
                         'our_challan': val1.order_id.id,
                         'product_id': val1.product_id.id,
                         # 'part_id': val1.part_id.id,
                         'part_no': val1.part_no,
                         'unit_id': val1.unit_id.id,
                         'sac_code': val1.product_id.category_id.hsn_no,
                         'qty': val1.qty,
                         'qty_nos': int(val1.qty) if ((val1.unit_id.name.lower())[0] == 'n') else 0,
                         'qty_kg': val1.qty if ((val1.unit_id.name.lower())[0] != 'n') else 0,
                         # 'unit_price': val1.unit_price,
                         'unit_price': job_rec_line.unit_price,
                         'tax_id': [(6, 0, [val1.tax_id.id])],
                         })

    def _compute_amount_words(self):
        words = ''
        words = num2words.num2words(self.total_amount, to='cardinal', lang='en_IN')

        words = words.title()
        self.amount_in_words = words

    def get_time(self):
        date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        date_time = datetime.strptime(date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5, minutes=30, seconds=0)
        date_time = date_time.strftime('%H:%M')
        return date_time

    name = fields.Char('Name', required=True)
    job_order_id = fields.Char('Order No.')
    job_order_date = fields.Char('Order Date')
    partner_id = fields.Many2one('my.partner', 'Party Name', required=True)
    # date = fields.Date('Date', default=fields.Date.today(), required=True)
    date = fields.Date(required=True, default=lambda self: self._get_current_date())

    @api.model
    def _get_current_date(self):
        """ :return current date """
        date = datetime.now() + timedelta(hours=5, minutes=30)
        date = date.date()        
        return date
        
    origin = fields.Char('Refecence')

    challan_bill_line = fields.One2many('challan.bill.line', 'order_id', 'Lines')
    user_id = fields.Many2one('res.users', 'Created By', default=lambda self: self.env.user)
    amount_untaxed = fields.Float(compute=_amount_all_wrapper, string='Untaxed Amount')
    tax_value = fields.Float(compute=_tax_amount, string='Taxes')
    total_amount = fields.Float(compute=_get_total_amount, string='Total Amount')
    round_amount = fields.Float(compute=_get_total_amount, string="Round Amount")
    transportation_mode = fields.Many2one('transportation.mode', 'Transport Mode')
    vehicle_no = fields.Many2one('vehicle', 'Vehicle No')
    eway_bill = fields.Char('EwayBill')
    supply_date = fields.Date('Date of Supply')
    cgst_total = fields.Float(string='CGST Total', compute='_compute_cgst_total')
    igst_total = fields.Float(string='IGST Total', compute='_compute_cgst_total')
    sgst_total = fields.Float(string="SGST Total", compute='_compute_cgst_total')
    challan_issue = fields.Many2many('joborder.challan', string='Attach Issue Challan')
    amount_in_words = fields.Char('Amount in words', compute='_compute_amount_words')
    cartage_value = fields.Float('Cartage Value', default=0.0)
    payment_term_ids = fields.Integer()
    time = fields.Char('Time', default=get_time)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
    ], string='Status', readonly=True, copy=False, index=True, default='draft')

    # def get_challan_date(self):
    #     for line in self.challan_bill_line:
    #         job_date = self.env['joborder.challan.receipt'].search([('name','=',line.)])

    sql_constraints = [
        ('name', 'unique(name)', 'Challan  no. already exists!')
    ]


class ChallanBillLine(models.Model):
    _name = "challan.bill.line"
    #
    # @api.multi
    # def unlink(self):
    #     if self.env.user.id == self.env.ref('base.user_admin').id:
    #         return super(ChallanBillLine, self).unlink()
    #     else:
    #         raise ValidationError('You Can not delete a record')

    @api.onchange('product_id')
    def onchange_product_id(self):
        unit_price = 0.0
        rate = 0.0
        if self.product_id:
            self.unit_id = self.product_id.unit_id.id
            # self.part_id = self.product_id.part_id.id
            self.part_no = self.product_id.part_no
            self.unit_price = self.product_id.sale_price

    def get_subtotal(self):
        total_price = 0.00
        for val in self:
            if val.qty:
                total_price = (val.qty * val.unit_price)
                val.write({'price_subtotal1': total_price})
                val.price_subtotal = total_price

    order_id = fields.Many2one('challan.bill', 'Id', ondelete='cascade')
    party_challan = fields.Many2one('joborder.challan.receipt', 'Party Challan')
    our_challan = fields.Many2one('joborder.challan', string='Our Challan')
    product_id = fields.Many2one('my.product', 'Product')
    # part_id = fields.Many2one('part.number','Part No.')
    part_no = fields.Char('Part No.')
    sac_code = fields.Char("SAC Code", default='9988')
    unit_id = fields.Many2one('my.unit', 'UOM')
    qty = fields.Float('Quantity')
    unit_price = fields.Float('Unit Price')
    tax_id = fields.Many2many('my.tax', string='Taxes', )
    price_subtotal = fields.Float(compute=get_subtotal, string='Subtotal')
    price_subtotal1 = fields.Float(string='Subtotal')
    qty_nos = fields.Integer('Qty Nos')
    qty_kg = fields.Float('Qty_Kg')
    bq = fields.Float('Bal Qty')
    party_namesss = fields.Many2one('my.partner', 'Party Name', related="order_id.partner_id")
    party_datessss = fields.Date('Date', related="order_id.date")
    # challan_type = fields.Selection([('regular', 'Regular'), ('rework', 'Rework'), ('foc', 'FOC')], default='regular',
    #                                 string='Challan Type', related="party_challan.challan_type")

class SupplymentaryInvoice(models.Model):
    _name = 'supplymentary.invoice'

    product_name = fields.Many2one('my.product',string="Product Name")
    qty = fields.Float('Qty')
    old_rate = fields.Float('Rate')
    new_rate = fields.Float('New Rate')
    unit_price = fields.Float('Unit Price')
    value = fields.Float('Value',compute="calculate_value")
    tax = fields.Many2one('my.tax',string="Tax")

    # @api.multi
    # def unlink(self):
    #     if self.env.user.id == self.env.ref('base.user_admin').id:
    #         return super(SupplymentaryInvoice, self).unlink()
    #     else:
    #         raise ValidationError('You Can not delete a record')
    #
    @api.multi
    def unlink(self):
        if self.state == 'draft':
            return super(SupplymentaryInvoice, self).unlink()
        else:
            if self.state != 'draft' and self.env.user.id == self.env.ref('base.user_admin').id:
                return super(SupplymentaryInvoice, self).unlink()
            else:
                raise ValidationError('You Can not delete a record')

    @api.onchange('qty','old_rate','new_rate','tax')
    def calculate_unit_price(self):
        for val in self:
            if val.old_rate and val.new_rate:
                val.unit_price = (val.old_rate - val.new_rate)


    def calculate_value(self):
        for val in self:
            val.value = (val.old_rate - val.new_rate) * val.qty + ((val.old_rate - val.new_rate) * val.qty * val.tax.amt) / 100



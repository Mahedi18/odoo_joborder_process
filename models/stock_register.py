from odoo import api, fields, models,tools
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from io import BytesIO


class StockRegister(models.Model):
    _name = "stock.register"
    _order = 'id desc'

    def all_incomming(self, party):
        line_list = []
        line_list1 = []
        receive_obj = self.env['joborder.challan.receipt'].search(
            [('date', '>=', self.from_date), ('date', '<=', self.to_date), ('partner_id', '=', party)])
        for val in receive_obj:
            if val.joborder_challan_receipt_lines:
                for val1 in val.joborder_challan_receipt_lines:
                    line_list.append(val1.id)
                    if line_list:
                        line_list = list(set(line_list))
                        line_list1 = sorted(line_list)
        return line_list1

    def get_party(self):
        party_list = []
        party_list1 = []
        receive_obj = self.env['joborder.challan.receipt'].search(
            [('date', '>=', self.from_date), ('date', '<=', self.to_date), ('partner_id', '<=', self.partner_id.id)])
        for val in receive_obj:
            if val.partner_id:
                for val1 in val.partner_id:
                    party_list.append(val1.id)
                    if party_list:
                        party_list = list(set(party_list))
                        party_list1 = sorted(party_list)
        return party_list1
    def get_name_party(self,party_list1):
        if party_list1:
            party_obj = self.env['my.partner'].browse(party_list1)
            a = party_obj.name
        return a
    def get_date(self,line_list1):
        if line_list1:
            line_obj = self.env['joborder.challan.receipt.line'].browse(line_list1)
            a = line_obj.order_id.date

        return a
    def get_challan(self,line_list1):
        if line_list1:
            line_obj = self.env['joborder.challan.receipt.line'].browse(line_list1)
            a = line_obj.order_id.name
        return a
    def get_issue(self,challan):
        challan_list=[]
        challan_list1=[]
        if challan:
            challan_obj = self.env['challan.line'].search([('party_challan.name', '=',challan)])

            for val in challan_obj:
                challan_list.append(val.order_id.id)
                if challan_list:
                    challan_list = list(set(challan_list))
                    challan_list1 = sorted(challan_list)
            return challan_list1
    def get_issue_challan_product(self,challan,product):
        line_obj = None
        if challan:
            issue_challan_obj = self.env['joborder.challan'].browse(challan)
            line_obj = self.env['challan.line'].search([('product_id.name', '=',product),('order_id', '=',issue_challan_obj.id)])
        return line_obj
    def get_issue_challan(self,v):
        if v:
            issue_challan_obj = self.env['joborder.challan'].browse(v)
            a = issue_challan_obj.name

        return a
    def get_issue_challan_date(self,v):
        if v:
            issue_challan_obj = self.env['joborder.challan'].browse(v)
            a = issue_challan_obj.date

        return a
    def get_party_name(self,line_list1):
        if line_list1:
            line_obj = self.env['joborder.challan.receipt.line'].browse(line_list1)
            a = line_obj.order_id.partner_id.name
        return a
    def get_part_name(self,line_list1):
        if line_list1:
            line_obj = self.env['joborder.challan.receipt.line'].browse(line_list1)
            a = line_obj.product_id.name
        return a
    def get_receive_qty(self,line_list1):
        if line_list1:
            line_obj = self.env['joborder.challan.receipt.line'].browse(line_list1)
            a = line_obj.qty
        return a
    def get_remaining_qty(self,line_list1):
        if line_list1:
            line_obj = self.env['joborder.challan.receipt.line'].browse(line_list1)
            a = line_obj.qty_remaining
        return a
    def get_issue_qty(self,v,name):
        a = 0
        if v:
            issue_challan_obj = self.env['joborder.challan'].browse(v)

            line_obj = self.env['challan.line'].search([('product_id.name', '=',name),('order_id', '=',issue_challan_obj.id)])
            for val in line_obj:


                a = a + val.qty
        return a
    def get_rem_qty(self,issue,rec):
        total_issue = 0.0
        if issue and rec:
            total_issue = total_issue + issue
            total_rem = rec - total_issue
        return total_rem

    def action_stoc_in_hand_final(self, cr):
        self.action_party_challan_wise_stock()
        # self.action_get_issue_receive_datasummarytotal()
        self._cr.execute('delete from stock_product_summary')
        search_parem = ''
        search_parem_trans = """where order_id is not null and date between '{}' and '{}' """.format(self.from_date,
                                                                                                     self.to_date)
        search_parem_stock = """where order_id is not null and jm.date<='{}'""".format(self.to_date)
        data = []
        if self.challan_type:
            if self.challan_type != 'all':
                search_parem += """ and challan_type='{}'""".format(self.challan_type)

        if self.partner_id:
            search_parem += """ and partner_id={}""".format(self.partner_id.id)
            # search_parem.append(('order_id.partner_id', '=', self.partner_id.id))
        if self.product_id:
            search_parem += """ and product_id={}""".format(self.product_id.id)

            # search_parem.append(('product_id', '=', self.product_id.id))
        # print(search_parem, '============searcg')

        # search_parem

        # challan_issue_rec = self.env['challan.line'].search(search_parem)
        tools.sql.drop_view_if_exists(self._cr, 'view_stock_in_hand')
        sqlstr = """DROP VIEW IF EXISTS view_stock_in_hand;
    create or replace view view_stock_in_hand as
            SELECT jm.partner_id,jl.product_id,jl.unit_id,sum(qty) closing, 0.0 rec_qty, 0.0 issue_qty FROM joborder_challan_receipt_line jl
                inner join joborder_challan_receipt jm on jm.id=jl.order_id
                {0} {2}
                group by jm.partner_id,jl.product_id,unit_id
            UNION
            SELECT jm.partner_id,jl.product_id,jl.unit_id,0.0 closing, sum(qty) rec_qty, 0.0 issue_qty FROM joborder_challan_receipt_line jl
                inner join joborder_challan_receipt jm on jm.id=jl.order_id
                {1} {2}
                group by jm.partner_id,jl.product_id,unit_id
            UNION
            SELECT jm.partner_id,jl.product_id,jl.unit_id, -sum(qty) closing,0.0 rec_qty,0.0 issue_qty  FROM challan_line jl
                inner join joborder_challan jm on jm.id=jl.order_id
                {0} {2}
                group by jm.partner_id,jl.product_id,unit_id
            UNION         
            SELECT jm.partner_id,jl.product_id,jl.unit_id, 0.0 closing,0.0 rec_qty,sum(qty) issue_qty  FROM challan_line jl
                inner join joborder_challan jm on jm.id=jl.order_id
                {1} {2}
                group by jm.partner_id,jl.product_id,unit_id;

            select partner_id,product_id,unit_id,sum(rec_qty) rec_qty, sum(issue_qty) issue_qty, sum(closing) closing from view_stock_in_hand group by partner_id,product_id,unit_id;     

           """.format(search_parem_stock, search_parem_trans, search_parem)
        # print(self.to_date, '===========self.to_date============aaaaaaaaaa\n', sqlstr)
        self._cr.execute(sqlstr)

        result = self._cr.dictfetchall()  # return the data into the list of dictionary format
        # print(result, 'pppppppppppppSTOCK IN HAND result aaaaaaaaaa')
        # result = []
        self.stock_product_summary_ids = result

    def action_get_issue_data(self):  # Challan Issue Data
        self._cr.execute('delete from  challan_line_issue_stock')
        data = []
        search_parem = 'SELECT jc.id challan_line_id,* FROM challan_line cl  \nINNER JOIN joborder_challan jc on cl.order_id=jc.id \n'
        search_parem += """WHERE cl.order_id is not null and jc.date between '{}' and '{}' """.format(self.from_date,self.to_date)
        if self.challan_type:
            if self.challan_type != 'all':
                search_parem += """ and jc.challan_type='{}'""".format(self.challan_type)
        if self.partner_id:
            search_parem += """ and jc.partner_id={}""".format(self.partner_id.id)
        if self.product_id:
            search_parem += """ and jl.product_id={}""".format(self.product_id.id)
        # print(search_parem, '============searcg')
        self._cr.execute(search_parem)
        data = self._cr.dictfetchall()
        self.challan_line_id = data
        # print(data, '======challan_issue_data========')

    def action_get_receive_data(self):  # Challan Receive Data
        self._cr.execute('delete  from challan_receipt_line_stock')
        data = []
        search_parem = 'SELECT jc.id challan_receive_id,* FROM joborder_challan_receipt_line cl  \n' \
                       'INNER JOIN joborder_challan_receipt jc on cl.order_id=jc.id \n'
        search_parem += """WHERE cl.order_id is not null and jc.date between '{}' and '{}' """.format(self.from_date,self.to_date)
        if self.challan_type:
            if self.challan_type != 'all':
                search_parem += """ and jc.challan_type='{}'""".format(self.challan_type)
        if self.partner_id:
            search_parem += """ and jc.partner_id={}""".format(self.partner_id.id)
        if self.product_id:
            search_parem += """ and jl.product_id={}""".format(self.product_id.id)
        # print(search_parem, '============searcg')
        self._cr.execute(search_parem)
        data = self._cr.dictfetchall()
        self.challan_receive_line_id = data
        # print(data, '======challan_receipt_data========')
        # if self.challan_receive_line_id:
        #     for line in self.challan_receive_line_id:
        #         line.unlink()
        # search_parem = []
        # data = []
        # if self.challan_type:
        #     if self.challan_type != 'all':
        #         search_parem.append(('order_id.challan_type', '=', self.challan_type))
        # if self.from_date:
        #     search_parem.append(('order_id.date', '>=', self.from_date))
        # if self.to_date:
        #     search_parem.append(('order_id.date', '<=', self.to_date))
        # if self.partner_id:
        #     search_parem.append(('order_id.partner_id', '=', self.partner_id.id))
        # if self.product_id:
        #     search_parem.append(('product_id', '=', self.product_id.id))
        # print(search_parem, '============searcg joborder_challan_receipt_lineaaaaaaaaaa')
        # challan_receive_rec = self.env['joborder.challan.receipt.line'].search(search_parem)
        # print(challan_receive_rec, '===============challan receive recbbbbbbbbbbb')
        # for line in challan_receive_rec:
        #     data.append((0, 0, {
        #         'product_id': line.product_id.id,
        #         'unit_id': line.unit_id.id,
        #         # 'party_challan': line.party_challan.id,
        #         'challan_receive_id': line.order_id.id,
        #         'partner_id': line.order_id.partner_id.id,
        #         # 'billed': line.order_id.billed,
        #         'state': line.order_id.state,
        #         'qty': line.qty,
        #         'date': line.order_id.date
        #     }))
        # self.challan_receive_line_id = data
        # print(data, '======challan_receive_data========')

    def get_total_issue_receive(self):
        search_parem = []
        data = []
        product_list = []
        if self.total_issue_line:
            for line in self.total_issue_line:
                line.unlink()
        if self.challan_type:
            if self.challan_type != 'all':
                search_parem.append(('order_id.challan_type', '=', self.challan_type))
        if self.from_date:
            search_parem.append(('order_id.date', '>=', self.from_date))
        if self.to_date:
            search_parem.append(('order_id.date', '<=', self.to_date))
        if self.partner_id:
            search_parem.append(('order_id.partner_id', '=', self.partner_id.id))
        if self.product_id:
            search_parem.append(('product_id', '=', self.product_id.id))
        receive_rec = self.env['joborder.challan.receipt.line'].search(search_parem)
        # print(receive_rec, '==================receivve')
        for val in receive_rec:
            product_list.append(val.product_id.id)
        # print(product_list, '========================product')
        product_list = list(set(product_list))
        for product in product_list:
            rec_qty = 0.0
            issue_qty = 0.0
            if self.partner_id:
                receive = self.env['joborder.challan.receipt.line'].search(
                    [('order_id.partner_id', '=', self.partner_id.id), ('product_id', '=', product),
                     ('order_id.date', '>=', self.from_date), ('order_id.date', '<=', self.to_date)])
            else:
                receive = self.env['joborder.challan.receipt.line'].search(
                    [('product_id', '=', product),
                     ('order_id.date', '>=', self.from_date), ('order_id.date', '<=', self.to_date)])
            for a in receive:
                rec_qty += a.qty
                issue_qty += a.issue_qty
            data.append((0, 0, {
                'product_id': self.env['my.product'].search([('id', '=', product)]).id,
                'total_receive': rec_qty,
                'total_issue': issue_qty,
            }))
        self.total_issue_line = data

    def action_productsummarytotal(self):

        if self.stock_product_summary_ids:
            for q in self.stock_product_summary_ids:
                q.unlink()
        # stock_summary = self.env['stock.product.summary']
        result = []
        data = {}
        self.action_productsummary()
        if self.stock_register_line:
            for line in self.stock_register_line:
                if line.product_id.name in data:
                    data[line.product_id.name][0] += line.rec_qty
                    data[line.product_id.name][2] += line.issue_qty
                    data[line.product_id.name][3] += (line.rec_qty - line.issue_qty)
                else:
                    data[line.product_id.name] = [line.rec_qty, line.partner_id.name, line.issue_qty, line.qty_balnew,
                                                  line.unit_id.name]
            # data = SortedDict(data)
            for val in sorted(data):
                result.append((0, 0, {
                    'product_id': val,
                    'unit_id': data[val][4],
                    'rec_qty': data[val][0],
                    'issue_qty': data[val][2],
                    'qty_balnew': data[val][3]
                }))
            self.stock_product_summary_ids = result

        # return data

    def action_productsummarytotalDailyRecIssue(self):
        search_parem = []
        data = []
        if self.challan_type:
            if self.challan_type != 'all':
                search_parem.append(('order_id.challan_type', '=', self.challan_type))
        if self.from_date:
            search_parem.append(('order_id.date', '>=', self.from_date))
        if self.to_date:
            search_parem.append(('order_id.date', '<=', self.to_date))
        if self.partner_id:
            search_parem.append(('order_id.partner_id', '=', self.partner_id.id))
        if self.product_id:
            search_parem.append(('product_id', '=', self.product_id.id))
        # print(search_parem, '============searcg')
        search_parem.append(('order_id', '!=', False))
        challan_issue_rec = self.env['challan.line'].search(search_parem)
        if self.stock_product_summary_ids:
            for q in self.stock_product_summary_ids:
                q.unlink()
        # stock_summary = self.env['stock.product.summary']
        result = []
        data = {}
        self.action_productsummary()
        # self.env['joborder.challan.receipt.line']
        # issue_rec=self.env['challan_line']
        # issue_rec=self.challan_line_issue_stock
        # print('issue-rec========', challan_issue_rec)

        if self.stock_register_line:
            for line in self.stock_register_line:
                # print('stock.reg======',line.partner_id,line.partner_id.name)
                if line.product_id.name in data:
                    data[line.product_id.name][0] += line.rec_qty
                    data[line.product_id.name][2] += 0
                    # data[line.product_id.name][3] += (line.rec_qty - line.issue_qty)
                    data[line.product_id.name][3] += line.rec_qty
                    # data[line.product_id.name][5] = line.partner_id
                    # data[line.partner_id][4]=line.partner_id.name
                else:
                    data[line.product_id.name] = [line.rec_qty, line.product_id.name, 0, line.rec_qty,
                                                  line.unit_id.name, line.partner_id]
            if challan_issue_rec:

                for line in challan_issue_rec:
                    # print('challan_issue======', line.order_id.partner_id, line.order_id.partner_id.name)
                    if line.product_id.name in data:
                        data[line.product_id.name][0] += 0
                        data[line.product_id.name][2] += line.qty
                        data[line.product_id.name][3] -= line.qty

                        # data[line.product_id.name][5]=line.order_id.partner_id
                    else:
                        data[line.product_id.name] = [0, line.product_id.name, line.qty, line.qty * -1,
                                                      line.unit_id.name, line.order_id.partner_id]

            # data = SortedDict(data)
            for val in sorted(data):
                result.append((0, 0, {
                    'product_id': val,
                    'rec_qty': data[val][0],
                    'issue_qty': data[val][2],
                    'qty_balnew': data[val][3],
                    'unit_id': data[val][4],
                    'partner_id': data[val][5]
                }))
            self.stock_product_summary_ids = result

        # return data

    def action_party_challan_wise_stock(self):
        self._cr.execute('delete from  stock_register_line')
        # if self.stock_register_line:
        #     for line in self.stock_register_line:
        #         line.unlink()
        # if self.stock_product_summary_ids:
        #     for q in self.stock_product_summary_ids:
        #         q.unlink()
        search_parem = []

        if self.challan_type:
            if self.challan_type != 'all':
                search_parem.append(('order_id.challan_type', '=', self.challan_type))
        if self.party_challan:
            search_parem.append(('order_id.name', '=', str(self.party_challan.name)))
        if self.from_date:
            search_parem.append(('order_id.date', '>=', self.from_date))
        if self.to_date:
            search_parem.append(('order_id.date', '<=', self.to_date))
        if self.partner_id:
            search_parem.append(('order_id.partner_id', '=', self.partner_id.id))
        if self.challan_status == 'pending':
            search_parem.append(('order_id.total_bal', '>', 0))
        if self.challan_status == 'pendingparts':
            search_parem.append(('order_id.total_bal', '>', 0))
            search_parem.append(('bal_qtynew', '>', 0))
        if self.challan_status == 'cleared':
            search_parem.append(('order_id.total_bal', '=', 0))
            # search_parem.append(('remaining_qty', '=', 0))
        if self.product_id:
            search_parem.append(('product_id', '=', self.product_id.id))
            # search_parem_line.append(('product_id','=',self.product_id))

        challan_rec = self.env['joborder.challan.receipt.line'].search(search_parem)
        # print('=========search_parem_line=========', search_parem)
        # print(challan_rec, '=================challan')
        # challan_rec_line=self.env['joborder.challan.receipt.line'].search(search_parem_line)
        for val in challan_rec:

            search_parem_line = []
            res = self.env['challan.line'].search(
                [('product_id', '=', val.product_id.id), ('party_challan', '=', val.order_id.id),
                 ('order_id', '!=', False)])
            lst = []
            for e in res:
                lst.append(e.order_id.id)
            # lst=set(lst)
            # print(lst, '====================lst==================')
            # ourchallan field  = [(6,0,lst)]

            # search_parem_line.append('order_id','=',val.id)
            # print(val.id,'=========search_parem_line=========',search_parem_line)
            for data in val:
                # print(data, ' in lineaaaaaaaaaaaaaa')
                # if val.remaining_qty>0:
                self.env['stock.register.line'].create(
                    {
                        'order_id': self.id,
                        'partner_id': val.order_id.partner_id.id,
                        'party_challan': val.order_id.id,
                        'date': val.order_id.date,
                        'our_challans': [(6, 0, lst)],
                        'product_id': data.product_id.id,
                        'part_no': data.part_no,
                        'unit_id': data.unit_id.id,
                        'rec_qty': data.qty,
                        'issue_qty': data.issue_qty,
                        'qty_balnew': data.bal_qtynew,
                        # 'rem_qty': data.rem_qty,
                    })

    def action_fetch_data(self):
        a = 20
        pass

    @api.onchange('challan_type', 'partner_id', 'challan_status', 'party_challan')
    def onchange_action(self):
        result = []
        product_list = []
        search_parem = []
        if self.partner_id and self.from_date and self.to_date and self.challan_type:
            search_parem.append(('partner_id', '=', self.partner_id.id))
            search_parem.append(('date', '>=', self.from_date))
            search_parem.append(('date', '<=', self.to_date))
            search_parem.append(('challan_type', '=', self.challan_type))
            if self.challan_status:
                if self.challan_status == 'pending':
                    search_parem.append(('total_bal', '>', 0))
                elif self.challan_status == 'cleared':
                    search_parem.append(('total_bal', '=', 0))
        challan_rec = self.env['joborder.challan.receipt'].search(search_parem)
        for val in challan_rec:
            result.append(val.id)
        if self.party_challan:
            receipt_line_rec = self.env['joborder.challan.receipt.line'].search(
                [('order_id', '=', self.party_challan.id)])
            for rec in receipt_line_rec:
                product_list.append(rec.product_id.id)
        else:
            receipt_line_rec = self.env['joborder.challan.receipt.line'].search(
                [('order_id.partner_id', '=', self.partner_id.id)])
            for rec in receipt_line_rec:
                product_list.append(rec.product_id.id)
        return {'domain': {'party_challan': [('id', 'in', result)], 'product_id': [('id', 'in', product_list)]}}

    name = fields.Char('Issue No.', Default='Stock Register')
    from_date = fields.Date('From Date', required=True,
                            default=lambda self: fields.datetime.now().date())  # ,default='2000-01-01'
    to_date = fields.Date('To Date', required=True,
                          default=lambda self: fields.datetime.now().date())  # ,default=datetime.today()
    partner_id = fields.Many2one('my.partner', 'Party')  # ,required=True
    product_id = fields.Many2one('my.product', 'Product')
    party_challan = fields.Many2one('joborder.challan.receipt', 'Party Challan')
    challan_type = fields.Selection([('regular', 'Regular'), ('rework', 'Rework'), ('foc', 'FOC'), ('all', 'All')],
                                    default='rework',
                                    string='Challan Type', required=True)
    user_id = fields.Many2one('res.users', 'Created By', default=lambda self: self.env.user)
    stock_register_line = fields.One2many('stock.register.line', 'order_id', 'Line')
    challan_status = fields.Selection(
        [('pending', 'Pending-all parts'), ('pendingparts', 'Pending- parts'), ('cleared', 'Cleared'), ('all', 'All')],
        default='pending',
        string='Challan Status', required=True)
    file = fields.Binary('XLS File', readonly=True)
    # stock_in_hand_idss=fields.One2many('my.stock.in.hand','my_stock_in_hand_id',string='Stock In Hand')
    sih_ids = fields.One2many('my.stock.in.hand', 'sih_id', string='Stock In Hand')
    stock_product_summary_ids = fields.One2many('stock.product.summary', 'stock_product_summary_id',
                                                string='Product Summary')
    challan_line_id = fields.One2many('challan.line.issue.stock', 'stock_challan_id', string='Challan Issue Data')
    challan_receive_line_id = fields.One2many('challan.receipt.line.stock', 'stock_received_id',
                                              string='Challan Receive Data')
    total_issue_line = fields.One2many('total.bal', 'stock_register_id', string="Total Issue Line")



    # @api.multi
    # def write(self, values):
    #     text = self.read_from_doc()
    #     values['content'] = text
    #     library_write = super(Library, self).write(values)
    #     return library_write

class MyStockInHand(models.Model):
    _name = 'my.stock.in.hand'
    _order = 'partner_id,product_id'

    def calc_opening_balance(self):
        for val in self:
            val.opening=val.closing-val.rec_qty+val.iss_qty

    sih_id=fields.Many2one('stock.register', ondelete='cascade')
    name=fields.Char()
    partner_id=fields.Many2one('my_partner','Party')
    product_id=fields.Many2one('my.product','Product')
    unit_id=fields.Many2one('my.unit','UOM',)

    rec_qty=fields.Float('RecQty',digits=(16,2))
    iss_qty=fields.Float('IssQty',digits=(16,2))
    opening = fields.Float('Opening Balance', compute='calc_opening_balance')
    closing=fields.Float('Closing Balance',digits=(16,2))

    remarks=fields.Char()
class StockRegisterLine(models.Model):
    _name = "stock.register.line"
    _order = 'date asc'

    order_id = fields.Many2one('stock.register','Id',ondelete='cascade')
    partner_id = fields.Many2one('my.partner', 'Party')
    party_challan = fields.Many2one('joborder.challan.receipt','Party Challan')
    our_challan = fields.Many2one('joborder.challan', string='Our Challan')
    our_challans=fields.Many2many('joborder.challan', string='Our Challans')
    date = fields.Date('Date')
    product_id = fields.Many2one('my.product','Product')
    # part_id = fields.Many2one('part.number','Part No.')
    part_no=fields.Char('Part No.')
    # unit_id = fields.Many2one('my.uom','UOM')
    unit_id = fields.Many2one('my.unit', 'UOM')
    rec_qty = fields.Float('Rec.Qty.')
    issue_qty = fields.Float('Issue Qty.')
    rem_qty = fields.Float('Remaining Qty',compute='cal_remaining_qty_slotck_line')
    qty_balnew=fields.Float('Bal New')

    @api.depends('rec_qty','issue_qty')
    def cal_remaining_qty_slotck_line(self):
        for val in self:
            val.rem_qty = val.rec_qty - val.issue_qty

class StockProductSummary(models.Model):
    _name = 'stock.product.summary'
    _order = 'partner_id,product_id'

    def calc_opening_balance(self):
        for val in self:
            val.opening = val.closing - ( val.rec_qty -val.issue_qty)

    def calc_receive_issue_diff(self):
        for val in self:
            val.qty_balnew=val.rec_qty-val.issue_qty

    product_id = fields.Many2one('my.product','Product')
    rec_qty = fields.Float('Rec.Qty.')
    issue_qty = fields.Float('Issue Qty.')
    qty_balnew = fields.Float('Bal New' ,compute='calc_receive_issue_diff')
    unit_id = fields.Many2one('my.unit','UOM')
    stock_product_summary_id = fields.Many2one('stock.register', ondelete='cascade')
    partner_id = fields.Many2one('my.partner', 'Party')
    opening = fields.Float('Opening Balance', compute='calc_opening_balance')
    closing = fields.Float('Closing Balance', digits=(16, 2))

    remarks = fields.Char()
class JoborderchallanIssueTableStock(models.Model):
    _name = 'challan.line.issue.stock'
    _order = 'date desc'


    stock_challan_id = fields.Many2one('stock.register', ondelete='cascade')
    partner_id = fields.Many2one('my.partner',string="Party")
    party_challan =fields.Many2one('joborder.challan.receipt', 'Party Challan', ondelete='cascade')
    billed=fields.Boolean('Billed')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
    ], string='Status', readonly=True, copy=False, index=True, default='draft')
    date = fields.Date(string="Date")
    product_id = fields.Many2one('my.product','Product')
    unit_id = fields.Many2one('my.unit', 'UOM')
    qty = fields.Float('Qty.')
    challan_issue_id = fields.Many2one('joborder.challan' )
class JoborderchallanReceiptTableStock(models.Model):
    _name = 'challan.receipt.line.stock'
    _order = 'date desc'

    # challan_receipt_line_stock


    stock_received_id = fields.Many2one('stock.register', ondelete='cascade')
    partner_id = fields.Many2one('my.partner',string="Party")
    # party_challan =fields.Many2one('joborder.challan.receipt', 'Party Challan', ondelete='cascade')
    # billed=fields.Boolean('Billed')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
    ], string='Status', readonly=True, copy=False, index=True, default='draft')
    date = fields.Date(string="Date")
    product_id = fields.Many2one('my.product','Product')
    unit_id = fields.Many2one('my.unit', 'UOM')
    qty = fields.Float('Qty.')
    challan_receive_id = fields.Many2one('joborder.challan.receipt')


    # @api.multi
    # def unlink(self):
    #     if self.env.user.id == self.env.ref('base.user_admin').id:
    #         return super(JoborderchallanIssueTableStock, self).unlink()
    #     else:
    #         raise ValidationError('You Can not delete a record')
class TotalProductBalance(models.Model):
    _name = 'total.bal'

    product_id = fields.Many2one('my.product',string="Product Name")

    total_issue = fields.Float('Total Issue')
    total_receive = fields.Float('Total Receive')
    stock_register_id  = fields.Many2one('stock.register', ondelete='cascade')








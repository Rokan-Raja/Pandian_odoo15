# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import request
import pytz
from datetime import datetime
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger=logging.getLogger(__name__)
class AgsTransaction(http.Controller):
    @http.route('/ags/live', type='json',auth='public')
    def index(self, **kw):
        bills=[]
        trans=[]
        matched_bills=[]
        matched_trans=[]
        ist = pytz.timezone('Asia/Calcutta')
        
        _logger.info("User:%s" %request.env.user.allow_manual_matching)

        current_shift=request.env['pos.pos_shift'].search([('state','=','open')])
        #Get Latest Write Date
        request.env.cr.execute("""SELECT write_date FROM  ags_transaction_ags_transaction order by write_date desc LIMIT 1""")  
        latest_trans_write_date=request.env.cr.dictfetchall() 

        request.env.cr.execute("""SELECT write_date FROM  pos_order_line order by write_date desc LIMIT 1""")  
        latest_order_write_date=request.env.cr.dictfetchall()         

        request.env.cr.execute("""SELECT write_date FROM  sale_order_line order by write_date desc LIMIT 1""")  
        latest_saleOrder_write_date=request.env.cr.dictfetchall()  

	#Fetching Bills
        order_lines=request.env['pos.order.line'].search([
            ('state', 'in', ['new','pending']),
            ('order_id.session_id', 'in', current_shift.session_ids.ids),
            ('product_id.product_tmpl_id.ags_product', '=', True)])
        for order in order_lines:
               date_order=order.create_date
               localize_date_order = datetime.strftime(pytz.utc.localize(datetime.strptime(date_order,DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(ist),"%d/%m/%Y %H:%M:%S")
   
               bill_dict={'no':order['order_id']['name'],'prod':order['product_id']['product_tmpl_id']['name'],'qty':(order['qty']),'amt':order['net_amt'],'date':localize_date_order,'id':order['id'],'salesman':order['order_id']['user_id']['partner_id']['name']}
               bills.append(bill_dict)

        #Fetching Transactions
        transactions=request.env['ags_transaction.ags_transaction'].search([
            ('shift', '=', current_shift.id),
            ('state', 'in', ['new','pending'])])
        #seq = [x['write_date'] for x in transactions]
        #_logger.info("max trans %s:" %max(seq))
        for trans_row in transactions:

            trans_dict={'tid':trans_row['tran_id'],'date':trans_row['transaction_date'],'pump':trans_row['pump'],'nozzle':trans_row['nozzle'],'prod':trans_row['product'],'qty':trans_row['volume'],'amt':float(trans_row['amount']),'id':trans_row['id'],'irregular_trans':trans_row['is_irregular_trans']}
            trans.append(trans_dict)
            

        #Fetching Sale Orders
        sale_orders=request.env['sale.order.line'].search([
                     ('status', 'in', ['new','pending']),
                     ('order_id.shift', '=', current_shift.id),
                     ('order_id.state', '=', 'sale'),
                     ('product_id.product_tmpl_id.ags_product', '=', True)])
   
        for saleOrder in sale_orders:
            date_order=saleOrder.create_date
            localize_date_order = datetime.strftime(pytz.utc.localize(datetime.strptime(date_order,DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(ist),"%d/%m/%Y %H:%M:%S")
            saleOrder_dict={'no':saleOrder['order_id']['name'],'prod':saleOrder['product_id']['product_tmpl_id']['name'],'qty':(saleOrder['product_uom_qty']),'amt':saleOrder['price_subtotal'],'date':localize_date_order,'id':saleOrder['id'],'salesman':saleOrder['order_id']['user_id']['partner_id']['name']}
            bills.append(saleOrder_dict)

        scheduler_state=request.env['ir.cron'].search([('cron_name','=','Comparision scheduler')])
        
        emp=[]
        #Fetching users
        users=request.env['res.users'].search([('active','=',True)])
        for user in users:
            emp.append({'id':user.id,'name':user.partner_id.name})

        customer=[]
        #Fetching customers
        customers=request.env['res.partner'].search([('customer','=',True)])
        for cust in customers:
            customer.append({'id':cust.id,'name':cust.name})

        payment_type=[]
        #Fetching payment types
        types=request.env['company.payment.types'].search([])
        for pay_type in types:
            payment_type.append({'id':pay_type.id,'name':pay_type.name})

           
        bill_sort=sorted(list(bills), key=lambda k: k['date'], reverse=True) 
        trans_sort=sorted(list(trans), key=lambda k: k['date'], reverse=True)
        bill_tot={'bill_tot':round(sum(bill['amt'] for bill in bills),2)}
        trans_tot={'trans_tot':round(sum(tran['amt'] for tran in trans),2)}
        _logger.info("Customer:%s" %emp)
        allow_manual_matching = request.env.user.allow_manual_matching
        data = [bill_sort,trans_sort,bill_tot,trans_tot,latest_order_write_date,latest_trans_write_date,current_shift.id,scheduler_state.active,emp,customer,payment_type,
        latest_saleOrder_write_date,allow_manual_matching]
        return data

    @http.route('/ags/live/data_refresh', type='json',auth='public')
    def data_refresh(self, **post):
        latest_bill_date = (post['bill_date'])
        latest_trans_date = (post['trans_date'])
        latest_saleOrder_date=(post['saleOrder_date'])
        manual_match=(post['manual_match'])
        credit_or_card=(post['credit_or_card'])
        bills=[]
        trans=[]
        bills_matched=[]
        matched=[]
        ist = pytz.timezone('Asia/Calcutta')

        current_shift=request.env['pos.pos_shift'].search([('state','=','open')])
        if manual_match or credit_or_card:
           self.post_manual_match(manual_match,credit_or_card)

        #Get Latest Write Date
        request.env.cr.execute("""SELECT write_date FROM  ags_transaction_ags_transaction order by write_date desc LIMIT 1""")  
        latest_trans_write_date=request.env.cr.dictfetchall() 

        request.env.cr.execute("""SELECT write_date FROM  pos_order_line order by write_date desc LIMIT 1""") 
        latest_order_write_date=request.env.cr.dictfetchall()         

        request.env.cr.execute("""SELECT write_date FROM  sale_order_line order by write_date desc LIMIT 1""")
        latest_saleOrder_write_date=request.env.cr.dictfetchall()    

	#Fetching Bills
        order_lines=request.env['pos.order.line'].search([
            ('state', 'in', ['new','pending']),
            ('order_id.session_id', 'in', current_shift.session_ids.ids),
            ('product_id.product_tmpl_id.ags_product', '=', True),
            ('write_date', '>', latest_bill_date)])
        _logger.info("Fetched Bills:%s" %order_lines)
        for order in order_lines:
               date_order=order.create_date
               localize_date_order = datetime.strftime(pytz.utc.localize(datetime.strptime(date_order,DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(ist),"%d/%m/%Y %H:%M:%S")
               bill_dict={'no':order['order_id']['name'],'prod':order['product_id']['product_tmpl_id']['name'],'qty':(order['qty']),'amt':order['net_amt'],'date':localize_date_order,'id':order['id'],'salesman':order['order_id']['user_id']['partner_id']['name']}
               bills.append(bill_dict)

        #Fetching Transactions
        transactions=request.env['ags_transaction.ags_transaction'].search([
            ('shift', '=', current_shift.id),
            ('manual_match', '=', False),
            ('state', 'in', ['new','pending','matched']),
            ('write_date', '>', latest_trans_date)])
        _logger.info("Fetched Transactions:%s" %transactions)
    
        for trans_row in transactions:
            if trans_row.state == 'matched':
               trans_dict={'bill_no':trans_row['order_relation'],'tran_no':trans_row['tran_id'],'bill_amt':float(trans_row['bill_amt']),'trans_amt':float(trans_row['amount']),'bill_line': trans_row['order_line_relation']}
               matched.append(trans_dict)
            else:
               trans_dict={'tid':trans_row['tran_id'],'date':trans_row['transaction_date'],'pump':trans_row['pump'],'nozzle':trans_row['nozzle'],'prod':trans_row['product'],'qty':trans_row['volume'],'amt':float(trans_row['amount']),'id':trans_row['id'],'irregular_trans':trans_row['is_irregular_trans']}
               trans.append(trans_dict)
            

        #Fetching SaleOrders
        saleOrders=request.env['sale.order.line'].search([
            ('status', 'in', ['new','pending']),
            ('order_id.shift', '=', current_shift.id),
            ('order_id.state', '=', 'sale'),
            ('product_id.product_tmpl_id.ags_product', '=', True),
            ('write_date', '>', latest_saleOrder_date)])
 
        for saleOrder in saleOrders:
            date_order=saleOrder.create_date
            localize_date_order = datetime.strftime(pytz.utc.localize(datetime.strptime(date_order,DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(ist),"%d/%m/%Y %H:%M:%S")
            saleOrder_dict={'no':saleOrder['order_id']['name'],'prod':saleOrder['product_id']['product_tmpl_id']['name'],'qty':(saleOrder['product_uom_qty']),'amt':saleOrder['price_subtotal'],'date':localize_date_order,'id':saleOrder['id'],'salesman':saleOrder['order_id']['user_id']['partner_id']['name']}
            bills.append(saleOrder_dict)

        bill_sort=sorted(list(bills), key=lambda k: k['date']) 
        trans_sort=sorted(list(trans), key=lambda k: k['date'])
        bill_tot={'bill_tot':round(sum(bill['amt'] for bill in bills),2)}
        trans_tot={'trans_tot':round(sum(tran['amt'] for tran in trans),2)}

        data=[bill_sort,trans_sort,bill_tot,trans_tot,matched,latest_order_write_date,latest_trans_write_date,current_shift.id,latest_saleOrder_write_date]
        return data


    def post_manual_match(self,match,credit_or_cash):
        #ags_product_ids=request.env['product.template'].search([('ags_product','=',True)]).ids
        for line in match:
            trans=request.env['ags_transaction.ags_transaction'].search([('tran_id','=',match[line]['tran'])])
            _logger.info("INFO:Manual Match Args:%s" %match[line])
            _logger.info("INFO: Manual match on Bill: %s with Transaction: %s" %(match[line]['bill'],match[line]['tran']))
            trans.write({'order_relation':match[line]['bill'],'manual_match':True,'comment':match[line]['cmt'],'responsible_person':match[line]['responsible_person'],'order_line_relation': match[line]['bill_line']})
        for rec in credit_or_cash:
            trans=request.env['ags_transaction.ags_transaction'].search([('tran_id','=',credit_or_cash[rec]['tran'])])
            _logger.info("INFO: Manual match on Transaction: %s as %s" %(credit_or_cash[rec]['tran'],credit_or_cash[rec]['type']))
            trans.write({'trans_type':credit_or_cash[rec]['type'],'manual_match':True,'comment':credit_or_cash[rec]['cmt'],'bill_no':credit_or_cash[rec]['bill_no'],'customer_id':credit_or_cash[rec]['customer_id'],'payment_id':credit_or_cash[rec]['payment_id'],'payment_tid':credit_or_cash[rec]['payment_tid']})
            

    @http.route('/ags/automap/stop', type='json', auth='public')
    def stop_comparison_scheduler(self, **val):
        try:
            request.env.cr.execute("""SELECT id FROM ir_cron WHERE cron_name='Comparision scheduler' FOR UPDATE NOWAIT""", log_exceptions=False)
        except: 
            error="This cron task is currently being executed and may not be modified Please try again in a few minutes"
            return error
        status=val['state']
        request.env.cr.execute("""UPDATE ir_cron SET active=%s WHERE cron_name='Comparision scheduler' """ %status)  


    @http.route('/ags/shift/queue', type='json',auth='public')
    def shift_queue(self, **kw):
        bills=[]
        trans=[]
        ist = pytz.timezone('Asia/Calcutta')
        current_shift=request.env['pos.pos_shift'].search([('id','=',kw['shift'])])
        #_logger.info("request:%s" %shift)  
          #Fetching Bills
        order_lines=request.env['pos.order.line'].search([
            ('state', 'in', ['new','pending']),
            ('order_id.session_id', 'in', current_shift.session_ids.ids),
            ('product_id.product_tmpl_id.ags_product', '=', True)])
        for order in order_lines:
               date_order=order.create_date
               localize_date_order = datetime.strftime(pytz.utc.localize(datetime.strptime(date_order,DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(ist),"%d/%m/%Y %H:%M:%S")
               bill_dict={'no':order['order_id']['name'],'prod':order['product_id']['product_tmpl_id']['name'],'qty':(order['qty']),'amt':order['net_amt'],'date':localize_date_order,'id':order['id'],'salesman':order['order_id']['user_id']['partner_id']['name']}
               bills.append(bill_dict)

        #Fetching Transactions
        transactions=request.env['ags_transaction.ags_transaction'].search([
            ('shift', '=', current_shift.id),
            ('state', 'in', ['new','pending'])])
    
        for trans_row in transactions:
            trans_dict={'tid':trans_row['tran_id'],'date':trans_row['transaction_date'],'pump':trans_row['pump'],'nozzle':trans_row['nozzle'],'prod':trans_row['product'],'qty':trans_row['volume'],'amt':float(trans_row['amount']),'irregular_trans':trans_row['is_irregular_trans']}
            trans.append(trans_dict)

        #Fetching SaleOrders
        saleOrders=request.env['sale.order.line'].search([
            ('status', 'in', ['new','pending']),
            ('order_id.shift', '=', current_shift.id),
            ('order_id.state', '=', 'sale'),
            ('product_id.product_tmpl_id.ags_product', '=', True)])
 
        for saleOrder in saleOrders:
            date_order=saleOrder.create_date
            localize_date_order = datetime.strftime(pytz.utc.localize(datetime.strptime(date_order,DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(ist),"%d/%m/%Y %H:%M:%S")
            saleOrder_dict={'no':saleOrder['order_id']['name'],'prod':saleOrder['product_id']['product_tmpl_id']['name'],'qty':(saleOrder['product_uom_qty']),'amt':saleOrder['price_subtotal'],'date':localize_date_order,'id':saleOrder['id'],'salesman':saleOrder['order_id']['user_id']['partner_id']['name']}
            bills.append(saleOrder_dict)


        emp=[]
        #Fetching users
        users=request.env['res.users'].search([('active','=',True)])
        for user in users:
            emp.append({'id':user.id,'name':user.partner_id.name})

        customer=[]
        #Fetching customers
        customers=request.env['res.partner'].search([('customer','=',True)])
        for cust in customers:
            customer.append({'id':cust.id,'name':cust.name})

        payment_type=[]
        #Fetching payment types
        types=request.env['company.payment.types'].search([])
        for pay_type in types:
            payment_type.append({'id':pay_type.id,'name':pay_type.name})
            
           
        bill_sort=sorted(list(bills), key=lambda k: k['date'], reverse=True) 
        trans_sort=sorted(list(trans), key=lambda k: k['date'], reverse=True)
        bill_tot={'bill_tot':round(sum(bill['amt'] for bill in bills),2)}
        trans_tot={'trans_tot':round(sum(tran['amt'] for tran in trans),2)}
        allow_manual_matching = request.env.user.allow_manual_matching
        data={'bills':bill_sort,'trans':trans_sort,'bill_tot':bill_tot,'trans_tot':trans_tot,'emp':emp,'customer':customer,'payment_type':payment_type,'allow_manual_matching': allow_manual_matching}
        return data


    @http.route('/ags/shift/compare', type='json',auth='public')
    def ags_shift_compare(self, **post):
        shift=(post['shift'])
        request.env['pos.shift.compare'].process_shift_comparision(shift)
        return shift
        
    @http.route('/ags/remove_zero_value', type='json',auth='public')
    def ags_remove_zero_value(self, **post):
        shift=(post['shift'])
        request.env['pos.shift.compare'].remove_zero_value_transaction(shift)
        return shift
        
    @http.route('/ags/remove_all_match_amount', type='json',auth='public')
    def ags_remove_all_matching(self, **post):
        shift=(post['shift'])
        request.env['pos.shift.compare'].remove_all_matching(shift)
        return shift

    @http.route('/shift/queue/map', type='json',auth='public')
    def shift_queue_map(self, **post):
        manual_match=(post['manual_match'])
        credit_or_card=(post['credit_or_card'])
        if manual_match or credit_or_card:
           self.post_manual_match(manual_match,credit_or_card)






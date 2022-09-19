# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from collections import deque
import psycopg2
import pytz
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat

_logger = logging.getLogger(__name__)

matched_rec=[]

class shift_compare(models.Model):
    _name = 'pos.shift.compare'

    start_at = fields.Datetime('Start Time')
    stop_at = fields.Datetime('Stop Time')

    bill=deque()
    trans=deque()
    match_not_found=False
    no_new_item=False
    start_time=""
    stop_time=""
    #Fetching Orders
    @api.model
    def get_orders(self,shift):
        self.bill.clear()
        ist = pytz.timezone('Asia/Calcutta')
        current_shift=self.env['pos.pos_shift'].search([('id','=',shift)])
        order_lines=self.env['pos.order.line'].search([
            ('state', 'in', ['new','pending']),
            ('order_id.session_id', 'in', current_shift.session_ids.ids),
            ('product_id.product_tmpl_id.ags_product', '=', True)],order='id asc')

        _logger.info("SUCCESS:Fetched (%s) Orders from shift %s" %(len(order_lines),current_shift.id))
        for order in order_lines:
               date_order=order.create_date
               localize_date_order = datetime.strftime(pytz.utc.localize(datetime.strptime(date_order,DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(ist),"%d/%m/%Y %H:%M:%S")
               bill_dict={'no':order['order_id']['name'],'prod':order['product_id']['product_tmpl_id']['name'],'qty':(order['qty']),'amt':order['net_amt'],'date':localize_date_order,'order_date':order['order_id']['date_order'],'state':order['state'],'id':order['id'],'type':'pos'}
               self.bill.append(bill_dict)

        # Fetching of saleorders(Roja-->11-2-19)
        #*****Start
        sale_orders=self.env['sale.order.line'].search([
            ('status', 'in', ['new','pending']),
            ('order_id.shift', '=', current_shift.id),
            ('product_id.product_tmpl_id.ags_product', '=', True)],order='id asc')

        for saleOrder in sale_orders:
            date_order=saleOrder.create_date
            localize_date_order = datetime.strftime(pytz.utc.localize(datetime.strptime(date_order,DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(ist),"%d/%m/%Y %H:%M:%S")
            saleOrder_dict={'no':saleOrder['order_id']['name'],'prod':saleOrder['product_id']['product_tmpl_id']['name'],'qty':(saleOrder['product_uom_qty']),'amt':saleOrder['price_total'],'date':localize_date_order,'order_date':saleOrder['order_id']['date_order'],'state':saleOrder['status'],'id':saleOrder['id'],'type':'sale'}
            self.bill.append(saleOrder_dict)
        #***End 
        
        _logger.info("SUCCESS:Pushed Orders in Bill Queue")
    #Fetching Transactions
    @api.model
    def get_trans(self,shift):
        self.trans.clear()
        current_shift=self.env['pos.pos_shift'].search([('id','=',shift)])
        transactions=self.env['ags_transaction.ags_transaction'].search([
            ('shift', '=', current_shift.id),
            ('state', 'in', ['new','pending'])],order='id asc')
        _logger.info("SUCCESS:Fetched (%s) Transactions from shift %s" %(len(transactions),current_shift.id))
    
        for trans_row in transactions:
            trans_dict={'tid':trans_row['tran_id'],'date':trans_row['transaction_date'],'pump':trans_row['pump'],'nozzle':trans_row['nozzle'],'prod':trans_row['product'],'qty':trans_row['volume'],'amt':float(trans_row['amount']),'state':trans_row['state'],'id':trans_row['id']}
            self.trans.append(trans_dict)

        _logger.info("SUCCESS:Pushed Transaction in Transaction Queue")

    #Get first new state Bill
    @api.model
    def get_bill(self):
        for bill_counter,bill in enumerate(self.bill):
            if "new" in bill.values():
                _logger.info("GOT: New State Bill -> %s" % bill['no'])
                return {'bill_index':bill_counter,'bill':bill}
               
                
    #Get first pending state transaction
    @api.model
    def get_pending_transaction(self):
        for trans_counter,trans in enumerate(self.trans):
            if "pending" in trans.values():
                _logger.info("GOT: Pending State Transaction -> %s" % trans['tid'])
                return {'trans_index':trans_counter,'trans':trans}

    #Get first new state transaction
    @api.model
    def get_transaction(self):
        for trans_counter,trans in enumerate(self.trans):
            if "new" in trans.values():
                _logger.info("GOT: New State Transaction -> %s" % trans['tid'])
                return {'trans_index':trans_counter,'trans':trans}
    #Change the state of bill
    @api.model
    def change_bill_state(self,bill_to_compare,state):
        # *** Start(Roja--> 12-2-19)
        if bill_to_compare['type'] == 'sale':
           current_bill=self.env['sale.order.line'].search([('id','=',bill_to_compare['id'])])
           current_bill.write({'status':state})
        # *** End
        else:
           current_bill=self.env['pos.order.line'].search([('id','=',bill_to_compare['id'])])
           current_bill.write({'state':state})
        _logger.info("SUCCESS: Changed bill state %s=%s" % (bill_to_compare['no'],state))
    #Change the state of transaction
    @api.model
    def change_trans_state(self,trans_to_compare,state,bill_ref=None):
        current_trans=self.env['ags_transaction.ags_transaction'].search([('id','=',trans_to_compare['id'])])
        if bill_ref:
           current_trans.write({'state':state,'order_relation':bill_ref['no'],'order_date':bill_ref['order_date'],'bill_amt':bill_ref['amt']})
           _logger.info("SUCCESS: Changed Transaction state %s=%s" % (trans_to_compare['tid'],state))
        else:
           current_trans.write({'state':state})
           _logger.info("SUCCESS: Changed Transaction state %s=%s" % (trans_to_compare['tid'],state))


    #Load Matched
    @api.model
    def load_matched(self,bill,trans):
        matched_rec.append({'bill':bill['no'],'trans':trans['tid']})

    #Get Matched
    @api.model
    def get_matched(self):
        return matched_rec

    #Check max time delay
    @api.model
    def max_delay(self,billdate, transdate):
        _logger.info("Checking delay attains maximum")
        max_delay=False
        d1 = datetime.strptime(billdate, "%d/%m/%Y %H:%M:%S")
        d2 = datetime.strptime(transdate, "%d/%m/%Y %H:%M:%S")
        if billdate > transdate:
           delay=abs((d1 - d2).seconds)
        if transdate >= billdate:
           delay=abs((d2 - d1).seconds)
        delay_time=self.env['ags.config'].search([],limit=1).max_delay
        delay_time_in_secs=int(delay_time) *60
        if delay > delay_time_in_secs:
           _logger.info("DELAY:(%s secs)Exists Max Delay of %s Seconds" %(delay_time_in_secs, delay))
           max_delay=True
        else:
           _logger.info("NODELAY:(%s secs) NOT Exists Max Delay of %s Seconds" %(delay_time_in_secs, delay))
        return max_delay


    #Check match in transaction
    @api.model
    def checktrans(self,bill,consider_delay):
        _logger.info("Checking Transaction queue for matching")
        for trec in list(self.trans):
            if consider_delay:
                delayed=self.max_delay(bill['bill']['date'],trec['date'])
            else:
                delayed = False
            _logger.info("STATE: Delayed state --> %s" %delayed)
            if bill['bill']['prod'] == trec['prod']  and bill['bill']['amt'] == trec['amt'] and not delayed:
              _logger.info("SUCCESS: Match Found [%s,%s,%s,%s]=[%s,%s,%s,%s]" % (bill['bill']['no'],bill['bill']['prod'],bill['bill']['amt'],bill['bill']['date'],trec['tid'],trec['prod'],trec['amt'],trec['date']))
              self.change_bill_state(bill['bill'],'matched')
              self.change_trans_state(trec,'matched',bill['bill'])
              self.bill[bill['bill_index']]['state'] ='matched'
              trec['state']='matched'
              try:
                if consider_delay:
                    self.bill.remove(bill['bill'])
                self.trans.remove(trec)
                _logger.info("REMOVE:Removed Matched Bills & Transaction from Queue")
                return            
              except ValueError:
                pass  # do nothing!

    #Check match in Bills
    @api.model
    def checkbill(self,trans,consider_delay):
        _logger.info("Checking Bill queue for matching")
        for brec in list(self.bill):
            if consider_delay:
                delayed=self.max_delay(brec['date'],trans['trans']['date'])
            else:
                delayed = False
            _logger.info("STATE: Delayed state --> %s" %delayed)
            if trans['trans']['prod'] == brec['prod']  and trans['trans']['amt'] == brec['amt'] and not delayed:
              _logger.info("SUCCESS: Match Found [%s,%s,%s,%s]=[%s,%s,%s,%s]" % (brec['no'],brec['prod'],brec['amt'],brec['date'],trans['trans']['tid'],trans['trans']['prod'],trans['trans']['amt'],trans['trans']['date']))
              self.change_bill_state(brec,'matched')
              self.change_trans_state(trans['trans'],'matched',brec)
              self.trans[trans['trans_index']]['state'] ='matched'
              brec['state']='matched'
              try:
                self.trans.remove(trans['trans'])
                self.bill.remove(brec)
                _logger.info("REMOVE:Removed Matched Bills & Transaction from Queue")
                return 
              except ValueError:
                pass  # do nothing!
            
    def get_zero_valued_transaction(self,shift):
        """ Getting Zero Valued Transactions """
        transactions = self.env['ags_transaction.ags_transaction'].search([
            ('shift', '=', shift),
            ('state', 'in', ['new','pending']),
            ('amount','=', 0)],order='id asc')
        return transactions
            
    def remove_zero_value_transaction(self,shift):
        trans = self.get_zero_valued_transaction(shift)
        for tran in trans:
            tran.write({
                'trans_type': 'other',
                'comment': 'Zero Value Transaction',
                'state': 'matched',
                'auto_match': True,
            })
          
    def remove_all_matching(self,shift):
        self.get_orders(shift)
        self.get_trans(shift)
        for bill_counter,bill in enumerate(self.bill):
            bill_to_compare = {'bill_index':bill_counter,'bill':bill}
            _logger.info("INFO:Bill_to_compare:%s" %bill_to_compare)
            self.checktrans(bill_to_compare,consider_delay = False)
         
        
    def process_shift_comparision(self,shift, consider_delay=True):
        self.start_time=fields.Datetime.now()
        self.get_orders(shift)
        self.get_trans(shift)
        while(self.bill and self.trans and not self.match_not_found and not self.no_new_item):
          bill_to_compare=self.get_bill()
          trans_to_compare=self.get_transaction()
          _logger.info("SET: Bill to compare -> %s" % bill_to_compare)
          _logger.info("SET: Trans to compare -> %s" % trans_to_compare)
          if bill_to_compare and trans_to_compare:
             _logger.info("Checking Time stamp of bill and transaction")
             if bill_to_compare['bill']['date']  <= trans_to_compare['trans']['date']:
                _logger.info("RES:Transaction Date is Greater(Bill date:%s,Transaction date:%s)" %(bill_to_compare['bill']['date'],trans_to_compare['trans']['date']))
                state='pending'
                self.change_bill_state(bill_to_compare['bill'],state)
                bill_to_compare['bill']['state']=state
                self.checktrans(bill_to_compare,consider_delay)

             elif bill_to_compare['bill']['date']  > trans_to_compare['trans']['date']:
                  _logger.info("RES:Bill Date is Greater(Bill date:%s,Transaction date:%s)" %(bill_to_compare['bill']['date'],trans_to_compare['trans']['date'])) 
                  state='pending'
                  self.change_trans_state(trans_to_compare['trans'],state)
                  trans_to_compare['trans']['state']=state
                  self.checkbill(trans_to_compare,consider_delay)

          elif bill_to_compare and not trans_to_compare:
               _logger.info("No New State Transaction directly checking pending transaction for matching")
               state='pending'
               self.change_bill_state(bill_to_compare['bill'],state)
               bill_to_compare['bill']['state']=state
               self.checktrans(bill_to_compare,consider_delay)

          elif not bill_to_compare and trans_to_compare:
               _logger.info("No New State Bill directly checking pending orders for matching")
               state='pending'
               self.change_trans_state(trans_to_compare['trans'],state)
               trans_to_compare['trans']['state']=state
               self.checkbill(trans_to_compare,consider_delay)

          elif not bill_to_compare and not trans_to_compare:
              _logger.info("NO MATCH: Matching is not found")
              self.match_not_found=True

          _logger.info("GOTO:NEXT ITERATION")
        self.stop_time=fields.Datetime.now()
        self.env['pos.shift.compare'].create({'start_at':self.start_time,'stop_at':self.stop_time})   




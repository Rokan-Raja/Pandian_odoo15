# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError
from collections import deque
import psycopg2
import pytz
from datetime import datetime

_logger = logging.getLogger(__name__)


class POSProductTemplate(models.Model):
    _inherit = 'product.template'
    ags_product = fields.Boolean(string="Is AGS Product")

class ags_transaction(models.Model):
    _name = 'ags_transaction.ags_transaction'
    _order = 'id desc'

    bill=deque()
    trans=deque()

    tran_id=fields.Char()
    transaction_date=fields.Char()
    pump=fields.Float()
    nozzle=fields.Float()
    product=fields.Char()
    mop_type = fields.Char()
    unit_price = fields.Float()
    volume = fields.Float()
    amount = fields.Float()
    discount=fields.Float()
    netamount = fields.Float()
    start_tot= fields.Float()
    end_tot = fields.Float()
    order_relation=fields.Char()
    order_line_relation = fields.Char()
    order_date= fields.Datetime(string="Order Date")
    time_delay= fields.Float(string="Delay Time", store=True)
    state = fields.Selection([('new','New'),('pending', 'Pending'),('matched', 'Matched'),('no_match','No Match')],  default='new',copy=False, string="Status")
    manual_match=fields.Boolean("Is Manual Match")
    auto_match=fields.Boolean("Is Auto Match")
    trans_type=fields.Selection([('credit','Credit'),('card','Card'),('test','Test'),('other','Other')], string='Transaction Type')
    comment = fields.Text('Comments', help="A precise description for the reason of manual match")
    bill_amt=fields.Float()
    responsible_person=fields.Many2one('res.users',ondelete='cascade',string="Responsible Person for mismatch")
    bill_no=fields.Char('Bill Number')
    customer_id=fields.Many2one('res.partner',ondelete='cascade',string='Customer')
    payment_id=fields.Many2one('company.payment.types',ondelete='cascade',string='Payment Type')
    payment_tid=fields.Char('Payment TID')
    is_irregular_trans=fields.Boolean("Irregular Transaction")

    _sql_constraints= [('uniq_name', 'unique(tran_id)', "The Transaction id must be unique !")]


    @api.model
    def process_manual_match(self,vals):
        _logger.info("Manual Match Process")
        order=self.env['pos.order'].search([('name','=',vals['order_relation']),('session_id', 'in', self.shift.session_ids.ids)]) or self.env['sale.order'].search([('name','=',vals['order_relation']),('pos_session', 'in', self.shift.session_ids.ids)])
        ags_product_ids=self.env['product.template'].search([('ags_product','=',True)]).ids
        _logger.info("ags_product_ids:%s" %ags_product_ids)
        bill_amt=0.0
        if not order:
           raise UserError(_("Give a Valid Bill Number"))
        if order.state == 'sale':
           for line in order.order_line:
               if line.product_id.id in ags_product_ids:
                  _logger.info("line:%s" %line)
                  if str(line.id) == vals['order_line_relation']:
                      if line.status == "matched":
                         raise UserError(_("Bill is already Matched"))
                      bill_amt=line.price_total
                      line.write({'status':'matched'})
                      vals['order_date']=order.date_order
                      vals['bill_amt']=bill_amt
                      vals['state'] = 'matched'
        else:
          for line in order.lines:
            if line.product_id.id in ags_product_ids:
               _logger.info("line:%s" %line)
               if str(line.id) == vals['order_line_relation']:
                   if line.state == "matched":
                      raise UserError(_("Bill is already Matched"))
                   bill_amt=line.net_amt
                   line.write({'state':'matched'})
                   vals['order_date']=order.date_order
                   vals['bill_amt']=bill_amt 
                   vals['state'] = 'matched'
        
        return vals

      
    def write(self, vals):
        _logger.info("Bill AMount Presence:%s" %vals)
        if 'manual_match' in vals and 'trans_type' in vals:
           if vals['manual_match'] and not vals['trans_type']:
              vals=self.process_manual_match(vals)
              _logger.info("Value:%s" %vals)
              if not 'state' in vals:
                 raise UserError(_("Wrong Bill")) 
           elif vals['manual_match'] and vals['trans_type']:
              vals['state'] = 'matched'
        elif 'manual_match' in vals:
              vals=self.process_manual_match(vals)
              _logger.info("Value:%s" %vals)
              if not 'state' in vals:
                 raise UserError(_("Wrong Bill")) 
                    
        _logger.info("write %s" % (vals))
        res = super(ags_transaction, self).write(vals)
        
        return res




    @api.model
    def get_orders(self):
        ist = pytz.timezone('Asia/Calcutta')
        current_shift=self.env['pos.pos_shift'].search([('state','=','open')])
        order_lines=self.env['pos.order.line'].search([
            ('state', 'in', ['new','pending']),
            ('order_id.session_id', 'in', current_shift.session_ids.ids),
            ('product_id.product_tmpl_id.ags_product', '=', True)])
        for order in order_lines:
               date_order=order.create_date
               localize_date_order = datetime.strftime(pytz.utc.localize(datetime.strptime(date_order,DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(ist),"%d/%m/%Y %H:%M:%S")
               bill_dict={'no':order['order_id']['name'],'prod':order['product_id']['product_tmpl_id']['name'],'qty':(order['qty']),'amt':order['net_amt'],'date':localize_date_order}
               self.bill.append(bill_dict)


    @api.model
    def get_trans(self):
        current_shift=self.env['pos.pos_shift'].search([('state','=','open')])
        transactions=self.env['ags_transaction.ags_transaction'].search([
            ('shift', '=', current_shift.id)])
    
        for trans_row in transactions:
            trans_dict={'tid':trans_row['tran_id'],'date':trans_row['transaction_date'],'pump':trans_row['pump'],'nozzle':trans_row['nozzle'],'prod':trans_row['product'],'qty':trans_row['volume'],'amt':float(trans_row['amount'])}
            self.trans.append(trans_dict)


    @api.model
    def process_matching(self):
          bill_to_compare=self.get_orders()
          trans_to_compare=self.get_trans()


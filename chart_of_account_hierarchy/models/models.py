# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class chart_of_account_hierarchy(models.Model):
#     _name = 'chart_of_account_hierarchy.chart_of_account_hierarchy'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100
class AccountAccount(models.Model):
    _inherit = 'account.account'
    
    name = fields.Char(required=True, index=True,translate=True)
    parent_id = fields.Many2one('account.account', 'Parent Account')
    child_ids = fields.One2many('account.account', 'parent_id', 'Children')
    
class AccountJournal(models.Model):
    _inherit = 'account.journal'
    tam_code = fields.Char(string='Short Code',translate=True, help="The journal entries of this journal will be named using this prefix.")
    name = fields.Char(string='Journal Name', required=True,translate=True)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    name=fields.Char(translate=True)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    payment_type_mode = fields.Selection([('cheque', 'Cheque'), ('draft', 'Draft'), 
        ('efund', 'E-Fund'), ('neft', 'NEFT'), ('rtgs', 'RTGS'), ('cash', 'Cash'),('card','Card')],
    	default='cash', string='Payment mode',translate=True)
    cheque_id=fields.Many2one('payment.cheques',string='Cheque')


class HrExpense(models.Model):
    _inherit = 'hr.expense'
    tam_description = fields.Char(string='Expense Description in tamil',translate=True)

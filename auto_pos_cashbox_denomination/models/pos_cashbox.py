# -*- coding: utf-8 -*-
###################################################################################
#
#    Shorepointsystem Private Limited
#    Author: Roja (05-05-20)
#
#
###################################################################################
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccountBankStmtCashWizard(models.Model):
    _inherit = 'account.bank.statement.cashbox'
    
                
    def get_last_session_cashbox_lines(self, config):
        """ Last Session Closing Balance Denomination """
        
        lines = self.env['account.cashbox.line']
        last_session = self.env['pos.session'].search([('config_id','=',config),('state','=','closed')],order='id desc',limit=1)
        bank_statement = last_session.cash_register_id
        if bank_statement:
            if bank_statement.cashbox_end_id:
                lines = self.env['account.cashbox.line'].search([('cashbox_id', '=', bank_statement.cashbox_end_id.id)])
        return lines

    def get_opening_lines(self, statement):
        """ Getting Opening Cash Register Denomination """
        lines = self.env['account.cashbox.line']
        if statement:
            bank_statement = self.env['account.bank.statement'].search([('id','=',statement)])
            if bank_statement.cashbox_start_id:
                lines = self.env['account.cashbox.line'].search([('cashbox_id', '=', bank_statement.cashbox_start_id.id)])
        return lines
 

    @api.model
    def default_get(self,fields):
        vals = super(AccountBankStmtCashWizard, self).default_get(fields)
        config_id = self.env.context.get('default_pos_id')
        lines = list()
        if config_id:
            lines = self.env['account.cashbox.line'].search([('default_pos_id', '=', config_id)])
        if self.env.context.get('balance', False) == 'start':
            closing_lines = self.get_last_session_cashbox_lines(config_id)
            lines += closing_lines
            vals['cashbox_lines_ids'] = [[0, 0, {'coin_value': line.coin_value, 'number': line.number, 'subtotal': line.subtotal}] for line in lines]
        else:
            lines += self.get_opening_lines(self.env.context.get('bank_statement_id'))
            vals['cashbox_lines_ids'] = [[0, 0, {'coin_value': line.coin_value, 'number': 0, 'subtotal': 0.0}] for line in lines]
            
        return vals

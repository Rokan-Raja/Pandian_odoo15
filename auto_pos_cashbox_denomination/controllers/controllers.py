# -*- coding: utf-8 -*-
from odoo import http

# class AutoPosCashboxDenomination(http.Controller):
#     @http.route('/auto_pos_cashbox_denomination/auto_pos_cashbox_denomination/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/auto_pos_cashbox_denomination/auto_pos_cashbox_denomination/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('auto_pos_cashbox_denomination.listing', {
#             'root': '/auto_pos_cashbox_denomination/auto_pos_cashbox_denomination',
#             'objects': http.request.env['auto_pos_cashbox_denomination.auto_pos_cashbox_denomination'].search([]),
#         })

#     @http.route('/auto_pos_cashbox_denomination/auto_pos_cashbox_denomination/objects/<model("auto_pos_cashbox_denomination.auto_pos_cashbox_denomination"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('auto_pos_cashbox_denomination.object', {
#             'object': obj
#         })
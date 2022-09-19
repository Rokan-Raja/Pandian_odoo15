# -*- coding: utf-8 -*-
from odoo import http

# class ChartOfAccountHierarchy(http.Controller):
#     @http.route('/chart_of_account_hierarchy/chart_of_account_hierarchy/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/chart_of_account_hierarchy/chart_of_account_hierarchy/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('chart_of_account_hierarchy.listing', {
#             'root': '/chart_of_account_hierarchy/chart_of_account_hierarchy',
#             'objects': http.request.env['chart_of_account_hierarchy.chart_of_account_hierarchy'].search([]),
#         })

#     @http.route('/chart_of_account_hierarchy/chart_of_account_hierarchy/objects/<model("chart_of_account_hierarchy.chart_of_account_hierarchy"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('chart_of_account_hierarchy.object', {
#             'object': obj
#         })
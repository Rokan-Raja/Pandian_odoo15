# -*- coding: utf-8 -*-
###################################################################################
#
#    Shorepointsystem Private Limited
#    Author: Roja (2-1-19)
#
#
###################################################################################
import logging
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta
from functools import partial

import psycopg2
import pytz

from odoo import api, fields, models,tools, SUPERUSER_ID, _
from odoo.tools import float_is_zero
from odoo import exceptions, _
from odoo import http
from datetime import datetime


_logger = logging.getLogger(__name__)

class Payment(models.Model):
     _name = 'company.payment.types'
     _rec_name='name'
    
     name=fields.Char("Online Payment Type")
     company_id=fields.Many2one('res.company',ondelete='cascade',string='Company')


class ResCompany(models.Model):
    _inherit = 'res.company'
    payment_ids = fields.One2many('company.payment.types','company_id',string="Online Payment Type",required="True")

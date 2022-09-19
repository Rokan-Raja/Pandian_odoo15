# -*- coding: utf-8 -*-
###################################################################################
#
#    Shorepointsystem Private Limited
#    Author: Roja (16-04-20)
#
#
###################################################################################
import logging

from odoo import api, fields, models, tools

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    allow_manual_matching = fields.Boolean("Allow Live Comparision Manual Matching")

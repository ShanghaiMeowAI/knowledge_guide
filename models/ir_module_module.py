# -*- coding: utf-8 -*-
from odoo import api, models


class IrModuleModule(models.Model):
    _inherit = 'ir.module.module'

    @api.model
    def knowledge_guide_hide_odoo_knowledge_app(self):
        official_knowledge = self.sudo().search([('name', '=', 'knowledge')], limit=1)
        if not official_knowledge:
            return

        # 本地知识库由 knowledge_guide 提供，官方 knowledge 占位应用只会引导到 Odoo 付费升级页。
        official_knowledge.write({
            'application': False,
            'to_buy': False,
            'website': False,
        })

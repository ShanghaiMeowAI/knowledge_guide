# -*- coding: utf-8 -*-
import re

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class KnowledgeGuideBookCreateWizard(models.TransientModel):
    """Wizard to create a new book from a selection of existing pages.

    Triggered from the Knowledge Guide Pages list view, contextual
    "Action" menu. Pages already attached to another book block the
    creation: the user must release them or remove them from the
    selection.
    """
    _name = 'knowledge.guide.book.create.wizard'
    _description = 'Create Book from Selected Pages'

    name = fields.Char(
        string='Collection Name',
        required=True,
        help="Stores the combination used for the knowledge framework Wizad proceeding.")

    slug = fields.Char(
        string='URL Slug',
        required=True,
        help='Lowercase letters, digits and dashes only. '
             'Used in the public URL.',
    )

    page_ids = fields.Many2many(
        'knowledge.guide.page',
        string='Pages to Add',
        default=lambda self: self._default_page_ids(),
        help="Links the page(s) used by this operation wizard.")

    blocked_page_ids = fields.Many2many(
        'knowledge.guide.page',
        'knowledge_guide_book_create_wizard_blocked_rel',
        'wizard_id', 'page_id',
        string='Pages in Another Collection',
        compute='_compute_blocked_page_ids',
        help="Links the page(s) used by this operation Wizard.")

    has_blocked = fields.Boolean(compute='_compute_blocked_page_ids', help="Controls whether has blocked is enabled for the knowledge guide wizard processing.")

    def _default_page_ids(self):
        if self.env.context.get('active_model') != 'knowledge.guide.page':
            return [(6, 0, [])]
        return [(6, 0, self.env.context.get('active_ids') or [])]

    @api.depends('page_ids', 'page_ids.book_id')
    def _compute_blocked_page_ids(self):
        for wizard in self:
            blocked = wizard.page_ids.filtered(lambda p: p.book_id)
            wizard.blocked_page_ids = blocked
            wizard.has_blocked = bool(blocked)

    @api.onchange('name')
    def _onchange_name_set_slug(self):
        if self.name and not self.slug:
            slug = re.sub(r'[^a-z0-9]+', '-', self.name.lower()).strip('-')
            self.slug = slug or False

    def action_create_book(self):
        self.ensure_one()

        if not self.page_ids:
            raise ValidationError(_('Select at least one guide page.'))

        blocked = self.page_ids.filtered(lambda p: p.book_id)
        if blocked:
            details = '\n'.join(
                _('- %(page)s (current collection: %(collection)s)', page=p.name, collection=p.book_id.name)
                for p in blocked
            )
            raise ValidationError(_(
                'The following pages already belong to another guide collection and cannot be added again:\n%(details)s\n\n'
                'Remove these pages from their current collection or clear them from the selection.',
                details=details,
            ))

        book = self.env['knowledge.guide.book'].create({
            'name': self.name,
            'slug': self.slug,
        })
        self.page_ids.write({'book_id': book.id})

        return {
            'type': 'ir.actions.act_window',
            'name': _('Guide Collection'),
            'res_model': 'knowledge.guide.book',
            'res_id': book.id,
            'view_mode': 'form',
            'target': 'current',
        }

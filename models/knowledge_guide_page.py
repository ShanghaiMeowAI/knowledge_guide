# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class KnowledgeGuidePage(models.Model):
    """A documentation page belonging to a knowledge guide book.

    Each page represents a section of the guide with HTML content,
    a category and the user groups allowed to view it.

    A page can hold both an original content (typically shipped by the
    source module via XML data) and a custom override entered by the
    administrator. The displayed content is the override when present,
    otherwise the original.
    """
    _name = 'knowledge.guide.page'
    _description = 'Knowledge Guide Page'
    _order = 'sequence, category, name'

    name = fields.Char(
        string='标题',
        required=True,
        translate=True,
        help='Title of the section displayed in the guide.',
    )

    content_html = fields.Html(
        string='原始内容',
        sanitize=True,
        sanitize_form=False,
        translate=True,
        help='Content provided by the source module. '
             'Treat as read-only when a module source is set.',
    )

    custom_content_html = fields.Html(
        string='自定义内容',
        sanitize=True,
        sanitize_form=False,
        translate=True,
        help='Content written by the administrator. '
             'When set, it replaces the original content in the displayed guide.',
    )

    display_content_html = fields.Html(
        string='展示内容',
        compute='_compute_display_content_html',
        sanitize=False,
    )

    has_custom_content = fields.Boolean(
        compute='_compute_display_content_html',
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Display order (lower comes first).',
    )

    category = fields.Char(
        string='分类',
        required=True,
        default='General',
        translate=True,
        help='Section / category of the page (e.g. General, Sales, Inventory).',
    )

    module_source = fields.Char(
        string='来源模块',
        help='Technical name of the module providing this page (for traceability).',
        readonly=True,
    )

    group_ids = fields.Many2many(
        'res.groups',
        string='可见用户组',
        help='If empty, the page is visible to everyone. '
             'Otherwise only users belonging to one of these groups can see it.',
    )

    active = fields.Boolean(
        string='启用',
        default=True,
        help='Allows archiving sections without deleting them.',
    )

    icon = fields.Char(
        string='图标',
        default='fa-book',
        help='FontAwesome class for the icon (e.g. fa-book, fa-cog, fa-user).',
    )

    book_id = fields.Many2one(
        'knowledge.guide.book',
        string='指南合集',
        ondelete='set null',
        index=True,
        help='Book this page belongs to (optional).',
    )

    action_link_ids = fields.One2many(
        'knowledge.guide.action.link',
        'page_id',
        string='Odoo 跳转按钮',
        help='Buttons displayed in the backend guide to jump to related Odoo pages.',
    )

    @api.depends('content_html', 'custom_content_html')
    def _compute_display_content_html(self):
        for record in self:
            if record.custom_content_html and record.custom_content_html.strip():
                record.display_content_html = record.custom_content_html
                record.has_custom_content = True
            else:
                record.display_content_html = record.content_html
                record.has_custom_content = False

    def action_view_source_html(self):
        """Open a transient wizard that shows the raw HTML of this page."""
        self.ensure_one()
        wizard = self.env['knowledge.guide.view.source.wizard'].create({
            'page_id': self.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('HTML source'),
            'res_model': 'knowledge.guide.view.source.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    @api.depends('name', 'category')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"[{record.category}] {record.name}"

    @api.model
    def _cleanup_legacy_sample_pages(self):
        """Archive old sample pages from the generic guide template.

        The current module data no longer ships those pages, but databases
        upgraded from an earlier draft may still have them. We archive instead
        of deleting to avoid destroying any administrator edits.
        """
        legacy_categories = {
            'getting started',
            'for administrators',
            'for developers',
        }
        legacy_names = {
            'welcome',
            'navigation',
        }
        legacy_content_markers = (
            'welcome to your knowledge guide',
            'sample page shipped with the knowledge guide module',
        )

        def _clean(value):
            return (value or '').strip().casefold()

        candidate_pages = self.with_context(active_test=False).search([
            ('module_source', 'in', [False, 'knowledge_guide']),
        ])
        legacy_pages = candidate_pages.filtered(
            lambda page: (
                _clean(page.category) in legacy_categories
                or (
                    _clean(page.name) in legacy_names
                    and _clean(page.category) in legacy_categories
                )
                or any(
                    marker in _clean(page.content_html)
                    for marker in legacy_content_markers
                )
            )
        )
        if legacy_pages:
            legacy_pages.write({'active': False})
        return True

class KnowledgeGuideActionLink(models.Model):
    """A backend jump button displayed on a guide page."""

    _name = 'knowledge.guide.action.link'
    _description = 'Knowledge Guide Action Link'
    _order = 'sequence, id'

    name = fields.Char(
        string='按钮文字',
        required=True,
        translate=True,
    )

    page_id = fields.Many2one(
        'knowledge.guide.page',
        string='指南页面',
        required=True,
        ondelete='cascade',
        index=True,
    )

    action_xmlid = fields.Char(
        string='动作 XMLID',
        required=True,
        help='External ID of the ir.actions record opened by this button.',
    )

    icon = fields.Char(
        string='图标',
        default='fa-external-link',
        help='FontAwesome class shown before the button text.',
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )

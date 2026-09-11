from types import SimpleNamespace
from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.addons.knowledge_guide.controllers.main import KnowledgeGuideController


@tagged('post_install', '-at_install')
class TestGuideReader(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Page = self.env['knowledge.guide.page']
        self.business = self.Page.create({'name': 'Reader needle business', 'content_html': '<p>Business body</p>'})
        self.reference = self.Page.create({'name': 'Reader needle reference', 'guide_kind': 'reference', 'content_html': '<p>Reference body</p>'})
        self.controller = KnowledgeGuideController()

    def request(self):
        return patch('odoo.addons.knowledge_guide.controllers.main.request', SimpleNamespace(env=self.env))

    def test_navigation_defaults_to_business_without_body(self):
        with self.request():
            result = self.controller.get_navigation(search_term='Reader needle')
        self.assertEqual([p['id'] for p in result['pages']], [self.business.id])
        self.assertNotIn('content_html', result['pages'][0])

    def test_all_search_business_first_and_detail_keeps_override(self):
        self.business.custom_content_html = '<p>Customer wording</p>'
        with self.request():
            result = self.controller.get_navigation(guide_kind='all', search_term='Reader needle')
            detail = self.controller.get_page(self.business.id)
        self.assertEqual([p['id'] for p in result['pages']], [self.business.id, self.reference.id])
        self.assertEqual(detail['content_html'], '<p>Customer wording</p>')

    def test_parent_cycle_and_cross_library_rejected(self):
        child = self.Page.create({'name': 'Child', 'parent_id': self.business.id})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.business.parent_id = child
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.reference.parent_id = self.business
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.business.guide_kind = 'reference'

    def test_restricted_related_pages_and_xmlid_lookup(self):
        hidden_group = self.env['res.groups'].create({'name': 'Guide hidden test group'})
        self.reference.group_ids = hidden_group
        self.business.related_page_ids = self.reference
        self.env['ir.model.data'].create({'module': 'knowledge_guide', 'name': 'reader_hidden', 'model': self.Page._name, 'res_id': self.reference.id})
        with self.request():
            self.assertFalse(self.controller.get_page(xmlid='knowledge_guide.reader_hidden'))
            self.assertEqual(self.controller.get_page(self.business.id)['related_pages'], [])
            self.assertFalse(self.controller.get_page(xmlid='base.main_company'))

    def test_legacy_endpoint_still_returns_body(self):
        with self.request():
            result = self.controller.get_pages(search_term='Reader needle business')
        self.assertEqual(result['pages'][0]['content_html'], '<p>Business body</p>')

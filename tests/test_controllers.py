# -*- coding: utf-8 -*-
from types import SimpleNamespace
from unittest.mock import patch

from werkzeug.exceptions import NotFound

from odoo.tests import TransactionCase, tagged

from odoo.addons.knowledge_guide.controllers.main import KnowledgeGuideController


@tagged('post_install', '-at_install', 'knowledge_guide')
class TestKnowledgeGuidePublicController(TransactionCase):
    """Tests for public guide controller behavior."""

    def setUp(self):
        super().setUp()
        self.controller = KnowledgeGuideController()
        self.Book = self.env['knowledge.guide.book']
        self.Page = self.env['knowledge.guide.page']

    def _request_patch(self):
        request = SimpleNamespace(env=self.env, db=self.env.cr.dbname)
        return patch('odoo.addons.knowledge_guide.controllers.main.request', request)

    def _make_published_book(self, slug='public-book'):
        old_books = self.Book.with_context(active_test=False).search([('slug', '=', slug)])
        old_books.mapped('page_ids').unlink()
        old_books.unlink()

        book = self.Book.create({
            'name': 'Public Book',
            'slug': slug,
            'is_published': True,
        })
        page = self.Page.create({
            'name': 'A page',
            'category': 'Default',
            'content_html': '<p>Hello reader</p>',
            'book_id': book.id,
        })
        return book, page

    def test_public_routes_are_registered(self):
        """The module contributes both public guide URL patterns."""
        self.env.registry.clear_cache('routing')
        routes = {str(rule) for rule in self.env['ir.http'].routing_map().iter_rules()}

        self.assertIn('/guide/<string:slug>', routes)
        self.assertIn('/guide/<string:slug>/<int:page_id>', routes)

    def test_page_to_json_includes_action_links(self):
        """Backend page payload includes configured Odoo action buttons."""
        page = self.Page.create({
            'name': 'Jump page',
            'category': 'Default',
            'content_html': '<p>Open something</p>',
        })
        link = self.env['knowledge.guide.action.link'].create({
            'page_id': page.id,
            'name': 'Open Customers',
            'action_xmlid': 'base.action_partner_form',
            'icon': 'fa-users',
            'sequence': 10,
        })

        data = self.controller._page_to_json(page)

        self.assertEqual(data['xmlid'], '')
        self.assertEqual(data['action_links'][0]['id'], link.id)
        self.assertEqual(data['action_links'][0]['action_xmlid'], 'base.action_partner_form')

    def test_page_to_json_includes_top_level_directory(self):
        page = self.Page.create({
            'name': 'Nested page',
            'section': 'Mail foundation',
            'section_sequence': 10,
            'category': 'Mailbox',
            'content_html': '<p>Nested navigation</p>',
        })

        data = self.controller._page_to_json(page)

        self.assertEqual(data['section'], 'Mail foundation')
        self.assertEqual(data['category'], 'Mailbox')
        self.assertFalse(data['is_section_overview'])
        self.assertFalse(data['is_default_landing'])

    def test_page_to_json_marks_section_overview(self):
        page = self.Page.create({
            'name': 'Mail overview',
            'section': 'Mail foundation',
            'section_sequence': 10,
            'category': 'Getting started',
            'is_section_overview': True,
        })

        data = self.controller._page_to_json(page)

        self.assertTrue(data['is_section_overview'])

    def test_page_to_json_marks_default_landing_page(self):
        page = self.Page.create({
            'name': 'Customer landing page',
            'section': 'Customer guide',
            'category': 'Overview',
            'is_default_landing': True,
        })

        data = self.controller._page_to_json(page)

        self.assertTrue(data['is_default_landing'])

    def test_public_navigation_groups_section_before_category(self):
        book, first_page = self._make_published_book(slug='nested-navigation')
        first_page.write({
            'section': 'Mail foundation',
            'section_sequence': 10,
            'category': 'Mailbox',
        })
        customer_page = self.Page.create({
            'name': 'Customer workflow',
            'section': 'Customer extension',
            'section_sequence': 20,
            'category': 'Sales',
            'content_html': '<p>Customer-specific content</p>',
            'book_id': book.id,
        })

        sections, pages = self.controller._get_book_pages_by_category(book)

        self.assertEqual(list(sections), ['Mail foundation', 'Customer extension'])
        self.assertEqual(list(sections['Mail foundation']), ['Mailbox'])
        self.assertEqual(sections['Mail foundation']['Mailbox'], [first_page])
        self.assertEqual(sections['Customer extension']['Sales'], [customer_page])
        self.assertEqual(list(pages), [first_page, customer_page])

    def test_page_to_json_includes_external_id_for_module_pages(self):
        """Backend page payload includes XMLID for guide chapter links."""
        page = self.Page.create({
            'name': 'External ID page',
            'category': 'Default',
            'content_html': '<p>Linked from another page</p>',
        })
        self.env['ir.model.data'].create({
            'module': 'knowledge_guide',
            'name': 'test_external_page',
            'model': 'knowledge.guide.page',
            'res_id': page.id,
        })

        data = self.controller._page_to_json(page)

        self.assertEqual(data['xmlid'], 'knowledge_guide.test_external_page')

    def test_get_published_book_with_valid_token(self):
        """A published book is returned when the token matches."""
        book, _page = self._make_published_book(slug='valid-token-book')

        with self._request_patch():
            result = self.controller._get_published_book(book.slug, book.access_token)

        self.assertEqual(result, book)

    def test_get_published_book_with_wrong_token_returns_404(self):
        """A wrong token must not grant access to the book."""
        book, _page = self._make_published_book(slug='wrong-token-book')

        with self._request_patch(), self.assertRaises(NotFound):
            self.controller._get_published_book(book.slug, 'not-the-real-token')

    def test_get_published_book_without_token_returns_404(self):
        """A request without any token must be rejected."""
        book, _page = self._make_published_book(slug='no-token-book')

        with self._request_patch(), self.assertRaises(NotFound):
            self.controller._get_published_book(book.slug, None)

    def test_get_published_book_unpublished_book_returns_404(self):
        """An existing but unpublished book must not be reachable."""
        book, _page = self._make_published_book(slug='unpublished-book')
        book.is_published = False

        with self._request_patch(), self.assertRaises(NotFound):
            self.controller._get_published_book(book.slug, book.access_token)

    def test_guide_book_public_selects_first_page(self):
        """The book URL renders the first active page by sequence."""
        book, first_page = self._make_published_book(slug='book-route')
        second_page = self.Page.create({
            'name': 'Second page',
            'category': 'Default',
            'sequence': 20,
            'content_html': '<p>Second</p>',
            'book_id': book.id,
        })

        with self._request_patch(), patch.object(
            self.controller, '_render_guide', return_value='rendered'
        ) as render:
            result = self.controller.guide_book_public(book.slug, token=book.access_token)

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data, b'rendered')
        (
            _book, _categories, all_pages, selected_page, prev_page, next_page,
            token, language_context,
        ) = render.call_args.args
        self.assertEqual(selected_page, first_page)
        self.assertEqual(list(all_pages), [first_page, second_page])
        self.assertFalse(prev_page)
        self.assertEqual(next_page, second_page)
        self.assertEqual(token, book.access_token)
        self.assertIn('current_lang', language_context)

    def test_guide_page_public_rejects_page_from_another_book(self):
        """A page ID from another guide must not be rendered."""
        book, _page = self._make_published_book(slug='page-route')
        other_book, other_page = self._make_published_book(slug='other-book')

        with self._request_patch(), self.assertRaises(NotFound):
            self.controller.guide_page_public(
                book.slug,
                other_page.id,
                token=book.access_token,
            )

        self.assertNotEqual(book, other_book)

    def test_guide_page_public_renders_valid_page(self):
        """The page-specific URL selects the requested page."""
        book, page = self._make_published_book(slug='valid-page-route')

        with self._request_patch(), patch.object(
            self.controller, '_render_guide', return_value='rendered'
        ) as render:
            result = self.controller.guide_page_public(
                book.slug,
                page.id,
                token=book.access_token,
            )

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data, b'rendered')
        (
            _book, _categories, _all_pages, selected_page, prev_page, next_page,
            token, language_context,
        ) = render.call_args.args
        self.assertEqual(selected_page, page)
        self.assertFalse(prev_page)
        self.assertFalse(next_page)
        self.assertEqual(token, book.access_token)
        self.assertIn('current_lang', language_context)

    def test_guide_page_public_accepts_manual_language(self):
        """A public guide URL can manually select any active Odoo language."""
        book, page = self._make_published_book(slug='manual-language-route')
        lang = self.env['res.lang'].search([('active', '=', True)], limit=1)

        with self._request_patch(), patch.object(
            self.controller, '_render_guide', return_value='rendered'
        ) as render:
            self.controller.guide_page_public(
                book.slug,
                page.id,
                token=book.access_token,
                lang=lang.code,
            )

        language_context = render.call_args.args[7]
        self.assertEqual(language_context['current_lang'], lang.code)

# -*- coding: utf-8 -*-
from collections import OrderedDict

from odoo import http
from odoo.http import request
from werkzeug.exceptions import NotFound


class KnowledgeGuideController(http.Controller):
    """Controller for the knowledge guide.

    Provides JSON-RPC routes for the OWL backend client action and HTTP
    routes for the public consumption of published books.
    """

    # ==================================================================
    # Backend routes (JSON-RPC, auth='user')
    # ==================================================================

    def _get_available_languages(self):
        """Return active Odoo languages available for guide rendering."""
        languages = request.env['res.lang'].sudo().search([('active', '=', True)])
        return [
            {
                'code': language.code,
                'name': language.name,
            }
            for language in languages
        ]

    def _get_language_context(self, requested_lang=None):
        """Resolve guide language from manual choice or the current user.

        The guide follows the logged-in user's language by default. When a
        reader manually chooses another active language, translated fields are
        read with that language in the Odoo context.
        """
        languages = self._get_available_languages()
        language_codes = {language['code'] for language in languages}
        user_lang = (
            request.env.user.lang
            or request.env.context.get('lang')
            or request.env['res.lang']._get_default_lang().code
        )

        if requested_lang in language_codes:
            current_lang = requested_lang
        elif user_lang in language_codes:
            current_lang = user_lang
        elif languages:
            current_lang = languages[0]['code']
        else:
            current_lang = user_lang

        return {
            'current_lang': current_lang,
            'user_lang': user_lang,
            'languages': languages,
        }

    def _page_to_json(self, page):
        """Serialize a guide page for the backend OWL client action."""
        xmlid = page.get_external_id().get(page.id, '')
        return {
            'id': page.id,
            'xmlid': xmlid,
            'name': page.name,
            'content_html': page.display_content_html or '',
            'section': page.section or '通用指南',
            'is_section_overview': page.is_section_overview,
            'is_default_landing': page.is_default_landing,
            'category': page.category,
            'icon': page.icon,
            'sequence': page.sequence,
            'module_source': page.module_source or '',
            'action_links': [
                {
                    'id': link.id,
                    'name': link.name,
                    'action_xmlid': link.action_xmlid,
                    'icon': link.icon or 'fa-external-link',
                    'sequence': link.sequence,
                }
                for link in page.action_link_ids.sorted()
            ],
        }

    @http.route('/knowledge_guide/get_pages', type='jsonrpc', auth='user')
    def get_pages(self, search_term=None, lang=None):
        """Return all pages the current user is allowed to see.

        Args:
            search_term (str, optional): text used to filter pages.

        Returns:
            dict: {
                'pages': [list of pages with their data],
                'categories': [unique categories]
            }
        """
        language_context = self._get_language_context(lang)
        user = request.env.user
        user_groups = user.group_ids.ids
        Page = request.env['knowledge.guide.page'].with_context(
            lang=language_context['current_lang']
        )

        domain = [
            ('active', '=', True),
            '|',
            ('group_ids', '=', False),
            ('group_ids', 'in', user_groups)
        ]

        if search_term:
            domain += [
                '|', '|',
                ('name', 'ilike', search_term),
                ('content_html', 'ilike', search_term),
                ('custom_content_html', 'ilike', search_term),
            ]

        pages = Page.search(domain)

        pages_data = []
        sections = []

        for page in pages:
            pages_data.append(self._page_to_json(page))
            if page.section not in sections:
                sections.append(page.section)

        return {
            'pages': pages_data,
            'sections': sections,
            'current_lang': language_context['current_lang'],
            'user_lang': language_context['user_lang'],
            'languages': language_context['languages'],
        }

    @http.route('/knowledge_guide/get_page', type='jsonrpc', auth='user')
    def get_page(self, page_id, lang=None):
        """Return a single page by ID, applying group-based access control."""
        language_context = self._get_language_context(lang)
        user = request.env.user
        user_groups = user.group_ids.ids

        page = request.env['knowledge.guide.page'].with_context(
            lang=language_context['current_lang']
        ).browse(page_id)

        if not page.exists() or not page.active:
            return False

        if page.group_ids and not any(g.id in user_groups for g in page.group_ids):
            return False

        return self._page_to_json(page)

    # ==================================================================
    # Public routes (HTTP, auth='public')
    # ==================================================================

    def _get_published_book(self, slug, token):
        """Fetch a published book and validate its access token.

        sudo() is justified here because the access is public; security
        relies on the unguessable UUID token.
        """
        if not token:
            raise NotFound()

        Book = request.env['knowledge.guide.book'].sudo()
        book = Book.search([
            ('slug', '=', slug),
            ('is_published', '=', True),
            ('active', '=', True),
        ], limit=1)

        if not book or book.access_token != token:
            raise NotFound()

        return book

    def _get_book_pages_by_category(self, book):
        """Group active pages as top-level directory, category, then page."""
        pages = book.page_ids.filtered('active').sorted(
            key=lambda p: (
                p.section_sequence,
                p.section or '',
                p.sequence,
                p.category or '',
                p.name,
            )
        )
        sections = OrderedDict()
        for page in pages:
            section = page.section or '通用指南'
            cat = page.category or 'General'
            sections.setdefault(section, OrderedDict()).setdefault(cat, []).append(page)
        return sections, pages

    @http.route(
        '/guide/<string:slug>',
        type='http',
        auth='public',
        website=False,
        csrf=False,
    )
    def guide_book_public(self, slug, token=None, **kwargs):
        """Render a published guide with the first page selected.

        URL: /guide/<slug>?token=<uuid>
        """
        language_context = self._get_language_context(kwargs.get('lang'))
        book = self._get_published_book(slug, token).with_context(
            lang=language_context['current_lang']
        )
        sections, all_pages = self._get_book_pages_by_category(book)

        selected_page = all_pages[0] if all_pages else None
        prev_page, next_page = self._get_prev_next(all_pages, selected_page)

        return self._render_guide(book, sections, all_pages, selected_page,
                                   prev_page, next_page, token, language_context)

    @http.route(
        '/guide/<string:slug>/<int:page_id>',
        type='http',
        auth='public',
        website=False,
        csrf=False,
    )
    def guide_page_public(self, slug, page_id, token=None, **kwargs):
        """Render a specific page of a published guide.

        URL: /guide/<slug>/<page_id>?token=<uuid>
        """
        language_context = self._get_language_context(kwargs.get('lang'))
        book = self._get_published_book(slug, token).with_context(
            lang=language_context['current_lang']
        )
        sections, all_pages = self._get_book_pages_by_category(book)

        selected_page = request.env['knowledge.guide.page'].sudo().with_context(
            lang=language_context['current_lang']
        ).browse(page_id)
        if not selected_page.exists() or selected_page.book_id != book or not selected_page.active:
            raise NotFound()

        prev_page, next_page = self._get_prev_next(all_pages, selected_page)

        return self._render_guide(book, sections, all_pages, selected_page,
                                   prev_page, next_page, token, language_context)

    def _render_guide(self, book, sections, all_pages, selected_page,
                      prev_page, next_page, token, language_context=None):
        """Render the public template prefixed with an HTML5 doctype.

        The DOCTYPE is not included in the QWeb template (it is not valid
        XML), so we prepend it manually to the rendered HTML.
        """
        language_context = language_context or self._get_language_context()
        response = request.render('knowledge_guide.guide_book_public', {
            'book': book,
            'sections': sections,
            'all_pages': all_pages,
            'selected_page': selected_page,
            'prev_page': prev_page,
            'next_page': next_page,
            'page_xmlids': {
                page.id: page.get_external_id().get(page.id, '')
                for page in all_pages
            },
            'token': token,
            'current_lang': language_context['current_lang'],
            'user_lang': language_context['user_lang'],
            'languages': language_context['languages'],
        })
        response.flatten()
        html_content = response.data
        if isinstance(html_content, bytes):
            html_content = html_content.decode('utf-8')
        html_content = '<!DOCTYPE html>\n' + html_content
        response.data = html_content.encode('utf-8')
        return response

    def _get_prev_next(self, all_pages, selected_page):
        """Return (previous_page, next_page) for in-guide navigation."""
        if not selected_page or not all_pages:
            return None, None

        page_list = list(all_pages)
        try:
            idx = page_list.index(selected_page)
        except ValueError:
            return None, None

        prev_page = page_list[idx - 1] if idx > 0 else None
        next_page = page_list[idx + 1] if idx < len(page_list) - 1 else None
        return prev_page, next_page

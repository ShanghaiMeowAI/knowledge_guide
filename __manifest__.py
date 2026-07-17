# -*- coding: utf-8 -*-
{
    'name': 'Knowledge Guide',
    'version': '19.0.1.7.2',
    'category': 'Productivity',
    'summary': 'Searchable, publishable, and shareable knowledge guide for Odoo users.',
    'description': """
Knowledge Guide
===============

This module provides a generic built-in knowledge base and user guide entry point.

Core Capabilities
-----------------
* Maintain guide pages by category with backend live search and content highlighting.
* Let administrators assemble pages into guide books and publish them through tokenized public links.
* Preserve module-provided content while allowing administrators to override the displayed version.
* Restrict backend guide visibility by user group.
* Generate link.tracker URLs to measure visits to public guides.
* Send guide links to multiple contacts through an email wizard.
* Allow other modules to contribute help pages through XML data files.

Use Cases
---------
* Internal user training and go-live guidance.
* Customer user manuals and feature explanations.
* Searchable and publishable help pages delivered alongside business modules.
    """,
    'author': '上海妙妙游智能科技有限公司',
    'maintainer': '上海妙妙游智能科技有限公司',
    'website': 'https://www.mmiao.net/',
    'copyright': '© 上海妙妙游智能科技有限公司 2026',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'link_tracker',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/knowledge_guide_book_create_wizard_views.xml',
        'views/knowledge_guide_book_views.xml',
        'views/knowledge_guide_page_views.xml',
        'views/knowledge_guide_menu.xml',
        'views/guide_public_templates.xml',
        'wizard/knowledge_guide_send_wizard_views.xml',
        'wizard/knowledge_guide_view_source_wizard_views.xml',
        'data/email_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'knowledge_guide/static/src/css/knowledge_guide.css',
            'knowledge_guide/static/src/js/knowledge_guide.js',
            'knowledge_guide/static/src/xml/knowledge_guide.xml',
        ],
    },
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

# -*- coding: utf-8 -*-
{
    'name': 'Knowledge Guide',
    'version': '19.0.1.6.3',
    'category': 'Productivity',
    'summary': '提供可搜索、可发布、可邮件分享的知识库指南。',
    'description': """
Knowledge Guide
===============

这个模块提供一个通用的内置知识库和用户指南入口。

核心能力
--------
* 按分类维护指南页面，支持后台实时搜索和内容高亮。
* 管理员可以把多个页面组成指南合集，并通过带 token 的公开链接发布。
* 保留模块原始内容，同时允许管理员通过自定义内容覆盖展示版本。
* 支持按用户组控制后台可见页面。
* 支持生成 link.tracker 跟踪链接，统计公开指南访问量。
* 支持邮件向导，将指南链接发送给多个联系人。
* 其他模块可以通过 XML 数据文件继续贡献自己的帮助页面。

适用场景
--------
* 内部用户培训和上线指引。
* 客户使用手册和功能说明。
* 业务模块交付时补充可搜索、可发布的帮助页面。
    """,
    'author': '上海妙妙游智能科技有限公司',
    'maintainer': '上海妙妙游智能科技有限公司',
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

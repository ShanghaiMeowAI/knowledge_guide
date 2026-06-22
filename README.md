# Knowledge Guide

`knowledge_guide` 是一个可复用的 Odoo 知识库指南模块。

模块只保留通用指南能力：后台页面搜索、指南合集、公开 token 链接、访问跟踪和邮件分享。模块本身不内置具体项目的使用手册；业务模块可以通过 XML 数据追加自己的指南页面。

## 功能

- 后台菜单：`使用指南`
- 管理员菜单：`设置 > 知识库指南 > 指南合集 / 指南页面`
- 页面模型：`knowledge.guide.page`
- 合集模型：`knowledge.guide.book`
- 公开访问：`/guide/<slug>?token=<uuid>`
- 支持通过 `link.tracker` 生成可统计的公开链接
- 支持通过邮件向导把指南链接发送给联系人
- 支持使用 `group_ids` 控制内部用户可见范围
- 支持通过 `knowledge.guide.action.link` 配置后台跳转按钮
- 支持依赖模块通过 XML 数据扩展指南页面

## 推荐使用方式

`knowledge_guide` 建议作为“指南基座模块”使用。后续给某个项目、客户或业务系统添加使用指南时，不要直接修改本模块，而是新建一个业务定制模块来继承它。

推荐流程：

1. 克隆本仓库，把 `knowledge_guide` 放入 Odoo addons 路径。

   ```bash
   git clone -b 19 https://github.com/ShanghaiMeowAI/knowledge_guide.git
   ```

2. 在同一个 addons 路径中新建一个业务指南模块，例如 `customer_x_knowledge_guide`。
3. 在新模块的 `__manifest__.py` 中依赖 `knowledge_guide`。
4. 在新模块的 XML 数据文件中创建指南合集、指南页面和跳转按钮。
5. 安装或升级业务指南模块，业务内容会追加到 `knowledge_guide` 提供的后台和公开指南能力中。

这种方式可以让 `knowledge_guide` 保持纯净通用，项目手册、客户培训内容、截图、业务跳转按钮都放在各自的定制模块里维护。

## 定制模块结构示例

```text
customer_x_knowledge_guide/
├── __init__.py
├── __manifest__.py
└── data/
    └── customer_x_guide.xml
```

`__manifest__.py` 示例：

```python
# -*- coding: utf-8 -*-
{
    'name': 'Customer X 使用指南',
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Customer X 项目的业务使用指南。',
    'depends': [
        'knowledge_guide',
    ],
    'data': [
        'data/customer_x_guide.xml',
    ],
    'installable': True,
    'application': False,
}
```

`__init__.py` 可以为空文件；如果定制模块只提供 XML 数据，不需要额外 Python 模型。

## 添加指南内容

业务定制模块可以通过 XML 创建自己的指南合集和页面：

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo noupdate="1">

    <record id="book_customer_x_user_guide" model="knowledge.guide.book">
        <field name="name">Customer X 使用指南</field>
        <field name="slug">customer-x-user-guide</field>
        <field name="sequence">10</field>
        <field name="description_html"><![CDATA[
            <p>本指南用于说明 Customer X 项目的日常操作流程。</p>
        ]]></field>
    </record>

    <record id="page_customer_x_overview" model="knowledge.guide.page">
        <field name="name">使用说明</field>
        <field name="category">入门</field>
        <field name="sequence">10</field>
        <field name="icon">fa-book</field>
        <field name="module_source">customer_x_knowledge_guide</field>
        <field name="book_id" ref="book_customer_x_user_guide"/>
        <field name="content_html"><![CDATA[
            <div class="user-guide-content">
                <h1>使用说明</h1>
                <p>这里编写项目自己的操作说明、注意事项和业务规则。</p>
            </div>
        ]]></field>
    </record>

</odoo>
```

字段说明：

- `knowledge.guide.book` 是指南合集，适合放一整套用户手册。
- `knowledge.guide.page` 是指南页面，页面可以单独存在，也可以通过 `book_id` 放入某个合集。
- `slug` 用于公开访问地址，例如 `/guide/customer-x-user-guide?token=<uuid>`。
- `module_source` 建议填写定制模块技术名，便于后续追踪页面来源。
- `content_html` 支持 HTML，推荐外层使用 `<div class="user-guide-content">` 以复用模块内置样式。
- `noupdate="1"` 适合默认手册数据，避免模块升级时覆盖管理员在数据库里的调整。

## 添加后台跳转按钮

如需在后台指南页面顶部显示“打开业务页面”之类的按钮，可以在定制模块中创建 `knowledge.guide.action.link` 记录：

```xml
<record id="page_customer_x_overview_action" model="knowledge.guide.action.link">
    <field name="page_id" ref="page_customer_x_overview"/>
    <field name="name">打开业务页面</field>
    <field name="action_xmlid">customer_x.customer_x_action</field>
    <field name="icon">fa-external-link</field>
    <field name="sequence">10</field>
</record>
```

`action_xmlid` 必须指向一个已经存在的 Odoo `ir.actions.*` 外部 ID。依赖的业务模块应在定制指南模块之前安装，或者由定制指南模块在 `depends` 中声明依赖。

## 在正文中添加链接

指南正文里也可以直接写 Odoo 后台链接：

```html
<a href="/web#action=customer_x.customer_x_action"
   target="_blank"
   rel="noopener">
    打开业务页面
</a>
```

后台动作链接适合内部用户使用；公开指南链接分享给外部读者时，应确认对方是否有对应系统权限。

## 安装和升级顺序

1. 安装 `knowledge_guide`。
2. 安装业务模块，例如 `customer_x`。
3. 安装业务指南模块，例如 `customer_x_knowledge_guide`。
4. 业务指南内容变化后，只升级业务指南模块，不需要修改或升级 `knowledge_guide` 基座模块。

## 维护说明

- 生产模块入口不要导入 `tests`；测试由 Odoo 测试加载器按需加载。
- 业务数据仍由各业务模块维护，本模块只保存指南内容和发布元数据。
- 公开链接使用 UUID token；重新生成 token 后旧链接会失效。
- 不要把项目专用手册、客户截图或业务跳转按钮直接提交到 `knowledge_guide`；这些内容应放入对应的业务指南定制模块。

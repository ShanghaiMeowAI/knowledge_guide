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

## 扩展方式

其他模块可以依赖 `knowledge_guide`，并提供自己的指南页面：

```xml
<record id="page_my_module" model="knowledge.guide.page">
    <field name="name">功能名称</field>
    <field name="category">分类</field>
    <field name="sequence">10</field>
    <field name="icon">fa-cog</field>
    <field name="module_source">my_module</field>
    <field name="content_html"><![CDATA[
        <div class="user-guide-content">
            <h1>功能名称</h1>
            <p>操作说明...</p>
        </div>
    ]]></field>
</record>
```

如需把页面放入某个指南合集，设置 `book_id` 即可。

如需在后台指南页面顶部显示跳转按钮，可以创建 `knowledge.guide.action.link` 记录：

```xml
<record id="page_my_module_action" model="knowledge.guide.action.link">
    <field name="page_id" ref="page_my_module"/>
    <field name="name">打开业务页面</field>
    <field name="action_xmlid">my_module.my_action</field>
    <field name="icon">fa-external-link</field>
    <field name="sequence">10</field>
</record>
```

## 维护说明

- 生产模块入口不要导入 `tests`；测试由 Odoo 测试加载器按需加载。
- 业务数据仍由各业务模块维护，本模块只保存指南内容和发布元数据。
- 公开链接使用 UUID token；重新生成 token 后旧链接会失效。

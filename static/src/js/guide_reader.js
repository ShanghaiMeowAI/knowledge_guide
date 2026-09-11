/** @odoo-module **/
import { markup, onWillDestroy, onPatched } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import KnowledgeGuide from "./knowledge_guide";

export function navigationTree(pages) {
    const nodes = new Map(pages.map(page => [page.id, { key: `page:${page.id}`, name: page.name, page, children: [] }]));
    const groups = new Map();
    const roots = [];
    for (const page of pages) {
        const node = nodes.get(page.id);
        if (nodes.has(page.parent_id)) {
            nodes.get(page.parent_id).children.push(node);
            continue;
        }
        const sectionKey = `${page.guide_kind}:${page.section}`;
        if (!groups.has(sectionKey)) {
            const section = { key: sectionKey, name: page.section, children: [] };
            groups.set(sectionKey, section);
            roots.push(section);
        }
        const section = groups.get(sectionKey);
        if (page.is_section_overview) {
            section.children.push(node);
        } else {
            const key = `${sectionKey}:${page.category}`;
            if (!groups.has(key)) {
                const category = { key, name: page.category, children: [] };
                groups.set(key, category);
                section.children.push(category);
            }
            groups.get(key).children.push(node);
        }
    }
    return roots;
}

// 复用原阅读器的业务动作、正文链接和高亮能力，只替换目录及正文加载流程。
export class GuideReader extends KnowledgeGuide {
    static template = "knowledge_guide.Reader";

    setup() {
        super.setup();
        Object.assign(this.state, { guideKind: "business", searchScope: "current", expandedNodes: [], contentLoading: false, contentError: false });
        this._navigationRequest = 0;
        this._contentRequest = 0;
        onWillDestroy(() => {
            clearTimeout(this._searchTimeout);
            this._navigationRequest++;
            this._contentRequest++;
        });
        onPatched(() => {
            if (this._pendingAnchor && !this.state.contentLoading) {
                this.scrollToContentAnchor(this._pendingAnchor);
                this._pendingAnchor = null;
            }
        });
    }

    async loadPages(searchTerm = "") {
        const request = ++this._navigationRequest;
        this.state.loading = true;
        this.state.error = false;
        try {
            const result = await rpc("/knowledge_guide/get_navigation", {
                guide_kind: searchTerm && this.state.searchScope === "all" ? "all" : this.state.guideKind,
                search_term: searchTerm || undefined, lang: this.state.currentLang || undefined,
            });
            if (request !== this._navigationRequest) return;
            this.state.pages = result.pages;
            this.state.currentLang = result.current_lang;
            this.state.languages = result.languages;
            if (!this.state.selectedPage && !searchTerm && result.pages.length) {
                await this.selectPage(result.pages.find(p => p.is_default_landing) || result.pages[0]);
            }
        } catch {
            if (request === this._navigationRequest) this.state.error = true;
        } finally {
            if (request === this._navigationRequest) this.state.loading = false;
        }
    }

    async switchGuide(kind) {
        clearTimeout(this._searchTimeout);
        this._contentRequest++;
        this.state.guideKind = kind;
        this.state.searchTerm = "";
        this.state.selectedPage = null;
        this.state.contentLoading = false;
        this.state.contentError = false;
        this.state.expandedNodes = [];
        await this.loadPages();
    }

    onScopeChange(ev) {
        this.state.searchScope = ev.target.value;
        clearTimeout(this._searchTimeout);
        this.loadPages(this.state.searchTerm);
    }

    async onLanguageChange(ev) {
        clearTimeout(this._searchTimeout);
        const selected = this.state.selectedPage;
        this._contentRequest++;
        this.state.currentLang = ev.target.value;
        window.localStorage.setItem("knowledge_guide_lang", ev.target.value);
        this.state.selectedPage = null;
        await this.loadPages(this.state.searchTerm);
        if (selected) await this.selectPage(selected);
    }

    async selectPage(page, anchor = "") {
        if (!page) return;
        const request = ++this._contentRequest;
        this.state.contentLoading = true;
        this.state.contentError = false;
        this._pendingAnchor = null;
        this.state.selectedPage = null;
        try {
            const result = await rpc("/knowledge_guide/get_page", {
                page_id: page.id, xmlid: page.xmlid || undefined, lang: this.state.currentLang || undefined,
            });
            if (request !== this._contentRequest) return;
            if (!result) throw new Error("Unavailable guide page");
            this.state.selectedPage = { ...result, content_html: markup(result.content_html || "") };
            if (result.guide_kind !== this.state.guideKind) {
                this.state.guideKind = result.guide_kind;
                this.state.searchTerm = "";
                await this.loadPages();
            }
            if (request !== this._contentRequest) return;
            const expand = (nodes, parents = []) => {
                for (const node of nodes) {
                    if (node.page?.id === result.id) this.state.expandedNodes = [...new Set([...this.state.expandedNodes, ...parents])];
                    expand(node.children, [...parents, node.key]);
                }
            };
            expand(navigationTree(this.state.pages));
            this._pendingAnchor = anchor;
            this.scrollContentToTop();
        } catch {
            if (request === this._contentRequest) {
                this.state.contentError = true;
                this._failedPage = page;
            }
        } finally {
            if (request === this._contentRequest) this.state.contentLoading = false;
        }
    }

    selectPageByXmlid(target) {
        const [xmlid, ...anchor] = target.split("#");
        // 关联阅读不依赖当前搜索结果，允许跨目录打开页面并定位段落。
        return this.selectPage({ xmlid }, anchor.join("#"));
    }

    onSearchInput(ev) {
        // 输入新关键词后立即使旧响应失效，避免防抖期间旧结果覆盖新查询。
        this._navigationRequest++;
        super.onSearchInput(ev);
    }

    get navigationRows() {
        if (this.state.searchTerm) return this.state.pages.map(page => ({ key: `page:${page.id}`, page, name: page.name, depth: 0, children: [] }));
        const rows = [];
        const walk = (nodes, depth) => {
            for (const node of nodes) {
                rows.push({ ...node, depth });
                if (this.state.expandedNodes.includes(node.key)) walk(node.children, depth + 1);
            }
        };
        walk(navigationTree(this.state.pages), 0);
        return rows;
    }

    toggleNode(key) {
        this.state.expandedNodes = this.state.expandedNodes.includes(key)
            ? this.state.expandedNodes.filter(value => value !== key) : [...this.state.expandedNodes, key];
    }

    guideLabel(kind) { return kind === "reference" ? _t("基础功能参考") : _t("业务操作指南"); }
}

registry.category("actions").add("knowledge_guide.main", GuideReader, { force: true });

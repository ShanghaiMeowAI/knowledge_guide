/** @odoo-module **/

import { Component, useState, onWillStart, onMounted, markup } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

/**
 * Knowledge Guide - Client Action OWL
 *
 * Main interface for the knowledge guide with a navigation sidebar
 * and a reading area rendering the HTML content of pages.
 */
class KnowledgeGuide extends Component {
    static template = "knowledge_guide.MainTemplate";

    setup() {
        this.notification = useService("notification");

        this.state = useState({
            pages: [],
            sections: [],
            selectedPage: null,
            searchTerm: "",
            currentLang: window.localStorage.getItem("knowledge_guide_lang") || "",
            userLang: "",
            languages: [],
            loading: true,
            error: false,
            expandedCategories: [],
            expandedSections: [],
        });

        onWillStart(async () => {
            await this.loadPages();
        });

        onMounted(() => {
            // Auto-select the first page on initial load when available
            if (this.state.pages.length > 0 && !this.state.selectedPage) {
                this.selectPage(this.state.pages[0]);
            }
        });
    }

    async loadPages(searchTerm = "") {
        try {
            this.state.loading = true;
            this.state.error = false;

            const result = await rpc("/knowledge_guide/get_pages", {
                search_term: searchTerm || undefined,
                lang: this.state.currentLang || undefined,
            });

            this.state.currentLang = result.current_lang || this.state.currentLang;
            this.state.userLang = result.user_lang || "";
            this.state.languages = result.languages || [];
            this.state.pages = result.pages.map((p) => ({
                ...p,
                section: p.section || _t("通用指南"),
                action_links: p.action_links || [],
                content_html: markup(p.content_html || ""),
            }));
            this.state.sections = result.sections || this.state.pages.reduce(
                (sections, page) => {
                    if (!sections.includes(page.section)) {
                        sections.push(page.section);
                    }
                    return sections;
                },
                []
            );
            this.state.loading = false;

            // When searching, do not auto-select.
            // If the currently selected page disappears, reset selection.
            if (this.state.selectedPage) {
                const pageStillExists = this.state.pages.find(
                    (p) => p.id === this.state.selectedPage.id
                );
                this.state.selectedPage = pageStillExists || null;
            }
        } catch (error) {
            console.error("Error loading knowledge guide pages:", error);
            this.state.error = true;
            this.state.loading = false;
        }
    }

    selectPage(page) {
        this.clearHighlights();

        this.state.selectedPage = page;

        if (page?.section && !this.isSectionExpanded(page.section)) {
            this.state.expandedSections = [...this.state.expandedSections, page.section];
        }
        const categoryKey = this.getCategoryKey(page?.section, page?.category);
        if (page?.category && !this.isCategoryExpanded(categoryKey)) {
            this.state.expandedCategories = [...this.state.expandedCategories, categoryKey];
        }

        setTimeout(() => {
            if (this.state.searchTerm) {
                this.highlightSearchTerm(this.state.searchTerm);
            }
        }, 50);
    }

    selectPageByXmlid(xmlid) {
        const page = this.state.pages.find((item) => item.xmlid === xmlid);
        if (!page) {
            this.notification.add(
                _t("The matching guide section was not found."),
                { type: "warning" }
            );
            return;
        }
        this.selectPage(page);
        this.scrollContentToTop();
    }

    scrollContentToTop() {
        const contentArea = document.querySelector(".user-guide-content-area");
        if (contentArea) {
            contentArea.scrollTo({ top: 0, behavior: "smooth" });
        }
    }

    scrollToContentAnchor(anchorId) {
        if (!anchorId) {
            return;
        }
        const target = document.getElementById(decodeURIComponent(anchorId));
        if (target && target.closest(".user-guide-content")) {
            target.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    }

    onContentClick(ev) {
        const link = ev.target.closest("a");
        if (!link) {
            return;
        }

        const rawHref = link.getAttribute("href") || "";
        const actionXmlid = link.dataset.guideActionXmlid || this.getActionXmlidFromHref(rawHref);
        if (actionXmlid) {
            ev.preventDefault();
            this.openOdooActionInNewTab(actionXmlid);
            return;
        }

        if (rawHref.startsWith("#guide:")) {
            ev.preventDefault();
            this.selectPageByXmlid(rawHref.slice("#guide:".length));
            return;
        }

        if (rawHref.startsWith("#") && rawHref.length > 1) {
            ev.preventDefault();
            this.scrollToContentAnchor(rawHref.slice(1));
        }
    }

    onSearchInput(ev) {
        const searchTerm = ev.target.value;
        this.state.searchTerm = searchTerm;

        // 300ms debounce
        clearTimeout(this._searchTimeout);
        this._searchTimeout = setTimeout(() => {
            this.loadPages(searchTerm);
        }, 300);
    }

    async onLanguageChange(ev) {
        const lang = ev.target.value;
        this.state.currentLang = lang;
        window.localStorage.setItem("knowledge_guide_lang", lang);
        await this.loadPages(this.state.searchTerm);
        if (this.state.selectedPage) {
            this.selectPage(this.state.selectedPage);
        }
    }

    getCategoriesBySection(section) {
        return this.state.pages
            .filter((page) => page.section === section)
            .reduce((categories, page) => {
                if (!categories.includes(page.category)) {
                    categories.push(page.category);
                }
                return categories;
            }, []);
    }

    getPagesBySectionCategory(section, category) {
        return this.state.pages.filter(
            (page) => page.section === section && page.category === category
        );
    }

    getCategoryKey(section, category) {
        return `${section || ""}::${category || ""}`;
    }

    isPageSelected(page) {
        return this.state.selectedPage && this.state.selectedPage.id === page.id;
    }

    toggleCategory(category) {
        if (this.isCategoryExpanded(category)) {
            this.state.expandedCategories = this.state.expandedCategories.filter(
                (item) => item !== category
            );
        } else {
            this.state.expandedCategories = [...this.state.expandedCategories, category];
        }
    }

    toggleSection(section) {
        if (this.isSectionExpanded(section)) {
            this.state.expandedSections = this.state.expandedSections.filter(
                (item) => item !== section
            );
        } else {
            this.state.expandedSections = [...this.state.expandedSections, section];
        }
    }

    buildOdooActionUrl(actionXmlid) {
        const url = new URL("/web", window.location.origin);
        const params = new URLSearchParams();
        params.set("action", actionXmlid);
        url.hash = params.toString();
        return url.toString();
    }

    getActionXmlidFromHref(rawHref) {
        if (!rawHref) {
            return "";
        }
        try {
            const url = new URL(rawHref, window.location.origin);
            const path = url.pathname.replace(/\/$/, "");
            if (url.origin !== window.location.origin || path !== "/web") {
                return "";
            }
            return new URLSearchParams(url.hash.slice(1)).get("action") || "";
        } catch {
            return "";
        }
    }

    openOdooActionInNewTab(actionXmlid) {
        if (!actionXmlid) {
            this.notification.add(
                _t("No target page is configured. Ask an administrator to check the guide button."),
                { type: "warning" }
            );
            return;
        }
        window.open(this.buildOdooActionUrl(actionXmlid), "_blank", "noopener");
    }

    openGuideAction(link) {
        this.openOdooActionInNewTab(link?.action_xmlid);
    }

    isCategoryExpanded(category) {
        return this.state.expandedCategories.includes(category);
    }

    isSectionExpanded(section) {
        return this.state.expandedSections.includes(section);
    }

    /**
     * Highlight all occurrences of the search term in the content area.
     */
    highlightSearchTerm(searchTerm) {
        if (!searchTerm || searchTerm.length < 2) {
            return;
        }

        const contentArea = document.querySelector('.user-guide-content');
        if (!contentArea) {
            return;
        }

        const escapedTerm = searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(escapedTerm, 'gi');

        const walker = document.createTreeWalker(
            contentArea,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: (node) => {
                    const parent = node.parentElement;
                    if (!parent ||
                        parent.tagName === 'SCRIPT' ||
                        parent.tagName === 'STYLE' ||
                        parent.classList.contains('search-highlight')) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    return regex.test(node.textContent)
                        ? NodeFilter.FILTER_ACCEPT
                        : NodeFilter.FILTER_REJECT;
                }
            }
        );

        const nodesToProcess = [];
        let currentNode;
        while (currentNode = walker.nextNode()) {
            nodesToProcess.push(currentNode);
        }

        let firstHighlight = null;

        nodesToProcess.forEach(textNode => {
            const parent = textNode.parentElement;
            const text = textNode.textContent;
            const fragment = document.createDocumentFragment();
            let lastIndex = 0;
            let match;

            regex.lastIndex = 0;

            while ((match = regex.exec(text)) !== null) {
                if (match.index > lastIndex) {
                    fragment.appendChild(
                        document.createTextNode(text.substring(lastIndex, match.index))
                    );
                }

                const mark = document.createElement('mark');
                mark.className = 'search-highlight';
                mark.textContent = match[0];
                fragment.appendChild(mark);

                if (!firstHighlight) {
                    firstHighlight = mark;
                }

                lastIndex = regex.lastIndex;
            }

            if (lastIndex < text.length) {
                fragment.appendChild(
                    document.createTextNode(text.substring(lastIndex))
                );
            }

            parent.replaceChild(fragment, textNode);
        });

        if (firstHighlight) {
            setTimeout(() => {
                firstHighlight.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            }, 100);
        }
    }

    clearHighlights() {
        const highlights = document.querySelectorAll('.search-highlight');
        highlights.forEach(mark => {
            const parent = mark.parentNode;
            const textNode = document.createTextNode(mark.textContent);
            parent.replaceChild(textNode, mark);
            parent.normalize();
        });
    }
}

registry.category("actions").add("knowledge_guide.main", KnowledgeGuide);

export default KnowledgeGuide;

/** @odoo-module **/
import { expect, test } from "@odoo/hoot";
import { navigationTree } from "@knowledge_guide/js/guide_reader";

const page = (id, extra = {}) => ({ id, name: `Page ${id}`, guide_kind: "business", section: "Business", category: "Work", parent_id: false, ...extra });

test("nested pages preserve source order and do not become duplicate roots", () => {
    const roots = navigationTree([page(1), page(2, { parent_id: 1 }), page(3, { parent_id: 2 })]);
    const parent = roots[0].children[0].children[0];
    expect(roots).toHaveLength(1);
    expect(parent.page.id).toBe(1);
    expect(parent.children[0].children[0].page.id).toBe(3);
});

test("a visible page remains discoverable when its parent is not visible", () => {
    const roots = navigationTree([page(2, { parent_id: 1 })]);
    expect(roots[0].children[0].children[0].page.id).toBe(2);
});

test("identical headings from separate libraries do not merge", () => {
    expect(navigationTree([page(1), page(2, { guide_kind: "reference" })])).toHaveLength(2);
});

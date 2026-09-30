const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
let Guide;
const source = fs.readFileSync(path.join(__dirname, '../static/src/js/knowledge_guide.js'), 'utf8')
    .replace(/^import .*;\r?\n/gm, '').replace('export default KnowledgeGuide;', '');
vm.runInNewContext(source, {
    Component: class {},
    registry: { category: () => ({ add: (_, component) => { Guide = component; } }) },
});
test('official ancestors, overview and seven children keep their order', () => {
    const guide = new Guide();
    const directory_path = ['Inventory', 'Warehouses and storage', 'Inventory management'];
    const titles = ['Warehouses', 'Locations', 'Operation types', 'Inventory adjustments', 'Cycle counts', 'Scrap inventory', 'Reception report'];
    guide.state = { pages: [
        { id: 1, section: 'Supply Chain', name: 'Inventory management', directory_path },
        ...titles.map((name, index) => ({ id: index + 2, section: 'Supply Chain', name, directory_path })),
        { id: 20, section: 'Supply Chain', name: 'Other guide', category: 'Legacy' },
    ] };
    const tree = guide.getDirectoryTree('Supply Chain');
    assert.equal(tree[0].name, 'Inventory');
    assert.equal(tree[0].children[0].name, 'Warehouses and storage');
    const management = tree[0].children[0].children[0];
    assert.equal(management.page.id, 1);
    assert.deepEqual(Array.from(management.children, node => node.name), titles);
    assert.deepEqual(Array.from(guide.getCategoriesBySection('Supply Chain')), ['Legacy']);
});

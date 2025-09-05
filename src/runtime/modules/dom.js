export function getDirectives(el) {
    const directives = [];
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_ELEMENT);
    while(walker.nextNode()) {
        const node = walker.currentNode;
        if (node.parentNode && node.parentNode.nodeName === 'TEMPLATE') continue;
        for (const attr of Array.from(node.attributes)) {
            if (attr.name.startsWith('x-')) {
                directives.push({ node, name: attr.name, value: attr.value });
            }
        }
    }
    const priority = ['for', 'if', 'init', 'ref'];
    return directives.sort((a, b) => {
        const aName = a.name.substring(2).split(':')[0];
        const bName = b.name.substring(2).split(':')[0];
        const aPrio = priority.includes(aName) ? priority.indexOf(aName) : priority.length;
        const bPrio = priority.includes(bName) ? priority.indexOf(bName) : priority.length;
        return aPrio - bPrio;
    });
}

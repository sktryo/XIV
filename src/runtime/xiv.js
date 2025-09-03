const XIV = {
    // The core reactive engine
    reactive(initialData, refs) {
        const effects = new Map();
        let currentEffect = null;

        const track = (key) => {
            if (currentEffect) {
                if (!effects.has(key)) {
                    effects.set(key, new Set());
                }
                effects.get(key).add(currentEffect);
            }
        };

        const trigger = (key) => {
            if (effects.has(key)) {
                effects.get(key).forEach(effect => effect());
            }
        };

        const scope = new Proxy(initialData, {
            get(target, key) {
                if (key === '$refs') return refs;
                if (key === '$fetch') {
                    return (url, options) => fetch(url, options).then(res => res.json());
                }
                track(key);
                return target[key];
            },
            set(target, key, value) {
                if (target[key] !== value) {
                    target[key] = value;
                    trigger(key);
                }
                return true;
            }
        });

        const createEffect = (fn) => {
            currentEffect = fn;
            fn();
            currentEffect = null;
        };

        return { scope, createEffect };
    },

    // Safely evaluate an expression within a scope
    safeEval(scope, expression) {
        try {
            return new Function('scope', `with(scope) { return ${expression} }`)(scope);
        } catch (error) {
            console.error(`XIV Error: Failed to evaluate expression "${expression}"`, error);
            return undefined;
        }
    },

    safeEvalNoReturn(scope, expression) {
        try {
            new Function('scope', `with(scope) { ${expression} }`)(scope);
        } catch (error) {
            console.error(`XIV Error: Failed to execute expression "${expression}"`, error);
        }
    },

    // Initialize a component
    initComponent(el) {
        const dataString = el.getAttribute('x-data') || '{}';
        const initialData = this.safeEval({}, dataString);
        if (initialData === undefined) return;

        const refs = {};
        const { scope, createEffect } = this.reactive(initialData, refs);

        // Handle x-init: runs once on initialization
        const initExpression = el.getAttribute('x-init');
        if (initExpression) {
            this.safeEvalNoReturn(scope, initExpression);
        }

        this.initDirectives(el, scope, createEffect, refs);
    },

    // Initialize all directives on an element and its children
    initDirectives(el, scope, createEffect, refs) {
        const directives = [];
        const walker = document.createTreeWalker(el, NodeFilter.SHOW_ELEMENT, { acceptNode: () => NodeFilter.FILTER_ACCEPT });

        while(walker.nextNode()) {
            const node = walker.currentNode;
            for (const attr of Array.from(node.attributes)) {
                if (attr.name.startsWith('x-')) {
                    directives.push({ node, name: attr.name, value: attr.value });
                }
            }
        }

        const priority = ['for', 'if', 'ref', 'init'];
        directives.sort((a, b) => {
            const aName = a.name.substring(2).split(':')[0];
            const bName = b.name.substring(2).split(':')[0];
            const aPrio = priority.includes(aName) ? priority.indexOf(aName) : priority.length;
            const bPrio = priority.includes(bName) ? priority.indexOf(bName) : priority.length;
            return aPrio - bPrio;
        });

        for (const { node, name, value } of directives) {
            if (!node.parentNode && name !== 'x-data') continue;

            const directive = name.substring(2);

            if (directive === 'ref') {
                refs[value] = node;
            } else if (directive === 'for') {
                const template = node;
                const match = value.match(/(.*)\s+in\s+(.*)/);
                if (!match) { console.error(`XIV Error: Invalid x-for expression: "${value}"`); continue; }
                const [_, alias, arrayKey] = match;
                const anchor = document.createComment(`xiv-for: ${value}`);
                template.parentNode.insertBefore(anchor, template);

                createEffect(() => {
                    const items = this.safeEval(scope, arrayKey) || [];
                    // Simple non-keyed update
                    while (anchor.nextSibling && anchor.nextSibling.hasAttribute && anchor.nextSibling.hasAttribute('data-xiv-for-item')) {
                        anchor.nextSibling.remove();
                    }

                    for (const item of items) {
                        const content = template.content.cloneNode(true);
                        const itemEl = content.firstElementChild;
                        itemEl.setAttribute('data-xiv-for-item', '');
                        
                        const newScope = Object.create(scope);
                        newScope[alias.trim()] = item;
                        this.initDirectives(itemEl, newScope, createEffect, refs);
                        anchor.parentNode.insertBefore(content, anchor.nextSibling);
                    }
                });
                template.remove();
            } else if (directive === 'if') {
                const template = node;
                const anchor = document.createComment('xiv-if');
                template.parentNode.insertBefore(anchor, template);
                let isShowing = false;
                let element = null;

                createEffect(() => {
                    const condition = this.safeEval(scope, value);
                    if (condition && !isShowing) {
                        const content = template.content.cloneNode(true);
                        element = content.firstElementChild;
                        this.initDirectives(element, scope, createEffect, refs);
                        anchor.parentNode.insertBefore(content, anchor.nextSibling);
                        isShowing = true;
                    } else if (!condition && isShowing) {
                        element.remove();
                        element = null;
                        isShowing = false;
                    }
                });
                template.remove();
            } else if (directive.startsWith('bind:')) {
                const attrName = directive.substring(5);
                createEffect(() => {
                    const result = this.safeEval(scope, value);
                    if (result === false || result === null || result === undefined) {
                        node.removeAttribute(attrName);
                    } else {
                        node.setAttribute(attrName, result === true ? '' : result);
                    }
                });
            } else if (directive.startsWith('on:')) {
                const event = directive.substring(3);
                node.addEventListener(event, (e) => {
                    const newScope = Object.create(scope);
                    newScope['$event'] = e;
                    this.safeEvalNoReturn(newScope, value);
                });
            } else if (directive === 'model') {
                const key = value;
                const eventType = (node.type === 'checkbox' || node.type === 'radio') ? 'change' : 'input';
                createEffect(() => { 
                    if (document.activeElement !== node) {
                        const modelValue = this.safeEval(scope, key);
                        if (node.type === 'checkbox') {
                            node.checked = modelValue;
                        } else {
                            node.value = modelValue;
                        }
                    }
                });
                node.addEventListener(eventType, (e) => {
                    this.safeEvalNoReturn(scope, `${key} = event.target.value`);
                });
            } else if (directive === 'text') {
                createEffect(() => {
                    node.textContent = this.safeEval(scope, value);
                });
            }
        }
    },

    init() {
        document.querySelectorAll('[x-data]').forEach(el => {
            this.initComponent(el);
        });
    }
};

class XTemp extends HTMLElement {
    constructor() { super(); this.attachShadow({ mode: 'open' }); }
    async connectedCallback() {
        const src = this.getAttribute('src');
        if (!src) { console.error('XIV Error: x-temp component requires a "src" attribute.'); return; }
        try {
            const response = await fetch(src);
            if (!response.ok) { throw new Error(`Failed to fetch template: ${response.statusText}`); }
            let templateText = await response.text();
            const props = {};
            for (const attr of this.attributes) {
                if (attr.name.startsWith('t-')) {
                    const propName = attr.name.substring(2);
                    props[propName] = attr.value;
                }
            }
            templateText = templateText.replace(/\{\{\s*(\w+)\s*\}\}/g, (match, propName) => props[propName] || '');
            templateText = templateText.replace(/<x-slot\s*\/>/g, '<slot></slot>');
            const template = document.createElement('template');
            template.innerHTML = templateText;
            this.shadowRoot.appendChild(template.content.cloneNode(true));
            this.shadowRoot.querySelectorAll('[x-data]').forEach(el => { XIV.initComponent(el); });
        } catch (error) { console.error(`XIV Error: Could not load template ${src}:`, error); }
    }
}

customElements.define('x-temp', XTemp);

document.addEventListener('DOMContentLoaded', () => {
    XIV.init();
});
import { reactive } from './modules/reactivity.js';
import { evaluate } from './modules/evaluate.js';
import { initDirectives } from './modules/directives.js';

const XIV = {
    start() {
        this.discoverComponents(document.body);
    },

    discoverComponents(rootEl) {
        const components = rootEl.querySelectorAll('[x-data]');
        components.forEach(el => this.initComponent(el));
    },

    initComponent(el) {
        if (el.__xiv_initialized) return;

        const dataString = el.getAttribute('x-data') || '{}';
        let initialData = {};
        try {
            initialData = new Function(`return ${dataString}`)();
        } catch (e) { return console.error('Error parsing x-data', e); }

        const refs = {};
        const { scope, createEffect } = reactive(initialData, refs);

        const initExpression = el.getAttribute('x-init');
        if (initExpression) {
            evaluate(scope, initExpression);
        }

        initDirectives(el, scope, createEffect, refs);
        el.__xiv_initialized = true;
    },
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
            XIV.discoverComponents(this.shadowRoot);
        } catch (error) { console.error(`XIV Error: Could not load template ${src}:`, error); }
    }
}

customElements.define('x-temp', XTemp);

document.addEventListener('DOMContentLoaded', () => {
    XIV.start();
});

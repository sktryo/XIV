const XIV = {
    init() {
        // Initialize all x-data components
        document.querySelectorAll('[x-data]').forEach(el => {
            this.initComponent(el);
        });

        // Initialize all x-temp components
        // This is handled by the custom element definition now.
    },

    initComponent(rootEl) {
        const dataString = rootEl.getAttribute('x-data');
        if (dataString === null) return;

        let data = {};
        try {
            data = (new Function(`return ${dataString}`))();
        } catch (e) {
            console.error('XIV Error: Invalid JSON in x-data attribute', e, dataString);
            return;
        }

        const scope = this.reactive(rootEl, data);
        this.registerEvents(rootEl, scope);
    },

    reactive(el, data) {
        const scope = new Proxy(data, {
            set: (target, key, value) => {
                target[key] = value;
                this.update(el, target);
                return true;
            }
        });
        this.update(el, scope);
        return scope;
    },

    update(el, scope) {
        const root = el.shadowRoot || el;

        // Update x-text elements
        root.querySelectorAll('[x-text]').forEach(textEl => {
            const key = textEl.getAttribute('x-text');
            if (key in scope) {
                textEl.textContent = scope[key];
            }
        });

        // Update x-model elements
        root.querySelectorAll('[x-model]').forEach(modelEl => {
            const key = modelEl.getAttribute('x-model');
            if (document.activeElement !== modelEl) {
                if (key in scope) {
                    modelEl.value = scope[key];
                }
            }
        });
    },

    registerEvents(el, scope) {
        const root = el.shadowRoot || el;
        const elementsWithEvents = [root, ...root.querySelectorAll('*')];

        elementsWithEvents.forEach(node => {
            if (!node.attributes) return;
            // Handle x-on directives
            for (const attr of node.attributes) {
                if (attr.name.startsWith('x-on:')) {
                    const event = attr.name.substring(5);
                    const expression = attr.value;
                    
                    node.addEventListener(event, () => {
                        try {
                            const func = new Function('scope', `with(scope) { ${expression} }`);
                            func(scope);
                        } catch (e) {
                            console.error(`XIV Error: Failed to execute expression "${expression}"`, e);
                        }
                    });
                }
            }

            // Handle x-model directive
            if (node.hasAttribute('x-model')) {
                const key = node.getAttribute('x-model');
                const eventType = (node.type === 'checkbox' || node.type === 'radio') ? 'change' : 'input';

                node.addEventListener(eventType, () => {
                    if (node.type === 'checkbox') {
                        scope[key] = node.checked;
                    } else {
                        scope[key] = node.value;
                    }
                });
            }
        });
    }
};

class XTemp extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
    }

    async connectedCallback() {
        const src = this.getAttribute('src');
        if (!src) {
            console.error('XIV Error: x-temp component requires a "src" attribute.');
            return;
        }

        try {
            const response = await fetch(src);
            if (!response.ok) {
                throw new Error(`Failed to fetch template: ${response.statusText}`);
            }
            let templateText = await response.text();

            // Extract props from t-* attributes
            const props = {};
            for (const attr of this.attributes) {
                if (attr.name.startsWith('t-')) {
                    const propName = attr.name.substring(2);
                    props[propName] = attr.value;
                }
            }

            // Replace {{...}} placeholders with prop values
            templateText = templateText.replace(/\{\{\s*(\w+)\s*\}\}/g, (match, propName) => {
                return props[propName] || '';
            });

            // Replace <x-slot> with <slot> for native Shadow DOM behavior
            templateText = templateText.replace(/<x-slot\s*\/>/g, '<slot></slot>');

            // Create a template element to parse the content
            const template = document.createElement('template');
            template.innerHTML = templateText;

            // Append the cloned template content to the shadow root
            this.shadowRoot.appendChild(template.content.cloneNode(true));

            // Initialize reactive features within the component's shadow DOM
            this.shadowRoot.querySelectorAll('[x-data]').forEach(el => {
                XIV.initComponent(el);
            });

        } catch (error) {
            console.error(`XIV Error: Could not load template ${src}:`, error);
        }
    }
}

customElements.define('x-temp', XTemp);

document.addEventListener('DOMContentLoaded', () => {
    XIV.init();
});

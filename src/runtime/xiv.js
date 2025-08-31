const XIV = {
    init() {
        document.querySelectorAll('[x-data]').forEach(el => {
            this.initComponent(el);
        });
    },

    initComponent(el) {
        const dataString = el.getAttribute('x-data');
        let data = {};
        try {
            data = (new Function(`return ${dataString}`))();
        } catch (e) {
            console.error('XIV Error: Invalid JSON in x-data attribute', e, dataString);
            return;
        }

        const scope = this.reactive(el, data);
        this.registerEvents(el, scope);
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
        // Update x-text elements
        el.querySelectorAll('[x-text]').forEach(textEl => {
            const key = textEl.getAttribute('x-text');
            if (key in scope) {
                textEl.textContent = scope[key];
            }
        });

        // Update x-model elements
        el.querySelectorAll('[x-model]').forEach(modelEl => {
            const key = modelEl.getAttribute('x-model');
            // Avoid updating the element that is currently being focused by the user
            // to prevent cursor jumps and IME issues.
            if (document.activeElement !== modelEl) {
                if (key in scope) {
                    modelEl.value = scope[key];
                }
            }
        });
    },

    registerEvents(el, scope) {
        const elementsWithEvents = [el, ...el.querySelectorAll('*')];
        elementsWithEvents.forEach(node => {
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

document.addEventListener('DOMContentLoaded', () => {
    XIV.init();
});
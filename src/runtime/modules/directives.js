import { evaluate } from './evaluate.js';
import { getDirectives } from './dom.js';

function _initDirectives(el, scope, createEffect, refs) {
    const directives = getDirectives(el);

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
            template.parentNode.replaceChild(anchor, template);

            createEffect(() => {
                const items = evaluate(scope, arrayKey) || [];
                while (anchor.nextSibling && anchor.nextSibling.__xiv_for_item) {
                    anchor.nextSibling.remove();
                }
                let lastEl = anchor;
                for (const item of items) {
                    const content = template.content.cloneNode(true);
                    const itemEl = content.firstElementChild;
                    if (!itemEl) continue;
                    itemEl.__xiv_for_item = true;
                    const newScope = Object.create(scope);
                    newScope[alias.trim()] = item;
                    _initDirectives(itemEl, newScope, createEffect, refs);
                    lastEl.after(itemEl);
                    lastEl = itemEl;
                }
            });
        } else if (directive === 'if') {
            const template = node;
            const anchor = document.createComment('xiv-if');
            template.parentNode.replaceChild(anchor, template);
            let isShowing = false;
            let element = null;
            createEffect(() => {
                const condition = evaluate(scope, value);
                if (condition && !isShowing) {
                    const content = template.content.cloneNode(true);
                    element = content.firstElementChild;
                    if (!element) return;
                    _initDirectives(element, scope, createEffect, refs);
                    anchor.after(element);
                    isShowing = true;
                } else if (!condition && isShowing) {
                    element.remove();
                    element = null;
                    isShowing = false;
                }
            });
        } else if (directive.startsWith('bind:')) {
            const attrName = directive.substring(5);
            createEffect(() => {
                const result = evaluate(scope, value);
                if (result === false || result === null || result === undefined) {
                    node.removeAttribute(attrName);
                } else {
                    node.setAttribute(attrName, result === true ? '' : result);
                }
            });
        } else if (directive.startsWith('on:')) {
            const event = directive.substring(3);
            node.addEventListener(event, (e) => {
                evaluate({ ...scope, '$event': e }, value);
            });
        } else if (directive === 'model') {
            const key = value;
            const eventType = (node.type === 'checkbox' || node.type === 'radio') ? 'change' : 'input';
            createEffect(() => { 
                if (document.activeElement !== node) {
                    const modelValue = evaluate(scope, key);
                    if (node.type === 'checkbox') node.checked = modelValue;
                    else node.value = modelValue;
                }
            });
            node.addEventListener(eventType, (e) => {
                const valueToSet = node.type === 'checkbox' ? e.target.checked : JSON.stringify(e.target.value);
                evaluate(scope, `${key} = ${valueToSet}`);
            });
        } else if (directive === 'text') {
            createEffect(() => {
                const textValue = evaluate(scope, value);
                node.textContent = (textValue === undefined || textValue === null) ? '' : textValue;
            });
        }
    }
}

export const initDirectives = _initDirectives;

export function reactive(initialData, refs) {
    const effects = new Map();
    let currentEffect = null;

    const track = (key) => {
        if (currentEffect) {
            if (!effects.has(key)) effects.set(key, new Set());
            effects.get(key).add(currentEffect);
        }
    };

    const trigger = (key) => {
        if (effects.has(key)) {
            effects.get(key).forEach(effect => effect());
        }
    };

    const scope = new Proxy(initialData, {
        get(target, key, receiver) {
            if (key === '$refs') return refs;
            if (key === '$fetch') return (url, options) => fetch(url, options).then(res => res.json());
            track(key);
            const value = Reflect.get(target, key, receiver);
            if (typeof value === 'function') {
                return value.bind(receiver);
            }
            return value;
        },
        set(target, key, value, receiver) {
            const success = Reflect.set(target, key, value, receiver);
            if (success) {
                trigger(key);
            }
            return success;
        }
    });

    const createEffect = (fn) => {
        const effect = () => {
            currentEffect = effect;
            fn();
            currentEffect = null;
        };
        effect();
    };

    return { scope, createEffect };
}

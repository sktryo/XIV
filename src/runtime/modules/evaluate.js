import { Parser } from 'expr-eval';

const parser = new Parser();

export function evaluate(scope, expression) {
    try {
        return parser.parse(expression).evaluate(scope);
    } catch (e) {
        console.error(`Error evaluating expression: "${expression}"`, e);
    }
}

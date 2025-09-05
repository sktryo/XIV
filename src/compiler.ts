import { file } from 'bun';
import path from 'path';
import { html as beautifyHtml } from 'js-beautify';

export class CompilerError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'CompilerError';
  }
}

export class XivCompiler {
  public async compile(mainFilePath: string, outputFilePath: string): Promise<string> {
    const normalizedMainFilePath = path.normalize(mainFilePath);

    const mainFile = file(normalizedMainFilePath);
    if (!(await mainFile.exists())) {
      throw new CompilerError(`Error: Main XIV file not found: ${normalizedMainFilePath}`);
    }

    let mainContentRaw: string;
    try {
      mainContentRaw = await mainFile.text();
    } catch (e) {
      throw new CompilerError(`Error reading main XIV file: ${e}`);
    }

    const runtimeScriptPath = path.relative(path.dirname(path.resolve(outputFilePath)), path.resolve('dist/runtime.js')).replace(/\\/g, '/');

    let headContent = '';
    let bodyContent = '';

    const mainMatch = mainContentRaw.match(/<xiv type="main">(.*?)<\/xiv>/s);
    let contentToParse = mainContentRaw;
    if (mainMatch) {
      contentToParse = mainMatch[1];
    }

    const headMatch = contentToParse.match(/<head>(.*?)<\/head>/s);
    if (headMatch) {
      headContent = headMatch[1];
    }

    const bodyMatch = contentToParse.match(/<body>(.*?)<\/body>/s);
    if (bodyMatch) {
      bodyContent = bodyMatch[1];
    } else if (!headMatch) {
      bodyContent = contentToParse;
    } else if (headMatch && !bodyMatch) {
      const headEndIndex = contentToParse.indexOf('</head>') + '</head>'.length;
      bodyContent = contentToParse.substring(headEndIndex).trim();
    }

    const hasTitle = /<title>/i.test(headContent);

    const finalHead = `<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    ${hasTitle ? '' : '<title>XIV App</title>'}
    ${headContent}
</head>`;

    const finalOutput = `<!DOCTYPE html>
<html lang="en">
${finalHead}
<body>
${bodyContent}
    <script src="${runtimeScriptPath}"></script>
</body>
</html>`;

    return beautifyHtml(finalOutput, {
      indent_size: 2,
      space_in_empty_paren: true,
    });
  }
}
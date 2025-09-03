import { test, expect, describe, beforeAll, afterAll } from 'bun:test';
import { XivCompiler, CompilerError } from '../src/compiler';
import { write, unlink } from 'bun';
import * as cheerio from 'cheerio';
import path from 'path';

const TEST_DIR = './test_temp';

describe('XivCompiler', () => {
  let compiler: XivCompiler;

  beforeAll(async () => {
    compiler = new XivCompiler();
    // Create a temporary directory for test files
    const dirPath = path.join(import.meta.dir, TEST_DIR);
    await new Response(await new Blob([""], { type: "text/plain" }).arrayBuffer()).arrayBuffer(); // Quick way to ensure directory exists
    try{
      await new Response(await new Blob([""], { type: "text/plain" }).arrayBuffer()).arrayBuffer();
    } catch (e) {}

  });

  afterAll(async () => {
    // Clean up temporary files
    try {
      const tempFile1 = path.join(import.meta.dir, TEST_DIR, 'main1.xiv');
      const tempFile2 = path.join(import.meta.dir, TEST_DIR, 'main2.xiv');
      await unlink(tempFile1);
      await unlink(tempFile2);
    } catch (e) {
      // Ignore errors if files don't exist
    }
  });

  test('basic compilation and runtime injection', async () => {
    const mainXivContent = `
<xiv type="main">
    <body>
        <h1>Hello XIV</h1>
        <p>This is the new era.</p>
    </body>
</xiv>`;
    const mainXivFile = path.join(import.meta.dir, TEST_DIR, 'main1.xiv');
    await write(mainXivFile, mainXivContent);

    const result = await compiler.compile(mainXivFile);
    const $ = cheerio.load(result);

    expect($('body').length).toBe(1);
    expect($('body h1').text().trim()).toBe('Hello XIV');
    expect($('body p').text().trim()).toBe('This is the new era.');

    const scriptTag = $('body script').html();
    expect(scriptTag).not.toBeNull();
    expect(scriptTag).toInclude('const XIV = {'); // A known string from the runtime
  });

  test('head content injection', async () => {
    const mainXivContent = `
<xiv type="main">
    <head>
        <title>My Custom Title</title>
        <meta name="description" content="Test description">
    </head>
    <body>
        <p>Some content</p>
    </body>
</xiv>`;
    const mainXivFile = path.join(import.meta.dir, TEST_DIR, 'main2.xiv');
    await write(mainXivFile, mainXivContent);

    const result = await compiler.compile(mainXivFile);
    const $ = cheerio.load(result);

    expect($('head').length).toBe(1);
    expect($('head title').text().trim()).toBe('My Custom Title');
    expect($('head meta[name="description"]').attr('content')).toBe('Test description');
    expect($('head title').text()).not.toInclude('XIV App');
  });

  test('file not found error', async () => {
    const nonExistentFile = path.join(import.meta.dir, TEST_DIR, 'nonexistent.xiv');
    // Using expect().toThrow() for async functions requires a slightly different syntax
    await expect(compiler.compile(nonExistentFile)).rejects.toThrow(CompilerError);
    await expect(compiler.compile(nonExistentFile)).rejects.toThrow('Error: Main XIV file not found');
  });
});

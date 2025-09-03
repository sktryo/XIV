#!/usr/bin/env bun

import { program } from 'commander';
import { XivCompiler, CompilerError } from './src/compiler';
import { write } from 'bun';
import path from 'path';

program
  .name('xiv')
  .description('A simple template engine for creating component-based HTML.')
  .version('1.0.0');

program
  .argument('<input_file>', 'The main XIV file to compile.')
  .option('-o, --output_file <path>', 'Path to the output HTML file', './index.html')
  .action(async (inputFile, options) => {
    console.log(`\n--- Starting XIV compilation ---`);
    console.log(`  Input file: ${inputFile}`);
    console.log(`  Output file: ${options.output_file}`);

    const compiler = new XivCompiler();

    try {
      const compiledHtml = await compiler.compile(inputFile);
      
      const outputPath = path.resolve(options.output_file);
      await write(outputPath, compiledHtml);

      console.log(`\n✅ Compilation successful. Output saved to '${options.output_file}'`);
      console.log("\n--- Compilation Result Preview (first 500 characters) ---");
      console.log(compiledHtml.substring(0, 500) + (compiledHtml.length > 500 ? "..." : ""));

    } catch (error) {
      if (error instanceof CompilerError) {
        console.error(`\n❌ Compilation failed: ${error.message}`);
      } else if (error instanceof Error) {
        console.error(`\n❌ An unexpected error occurred: ${error.message}`);
      } else {
        console.error(`\n❌ An unexpected and unknown error occurred.`);
      }
      process.exit(1);
    }
  });

program.parse(process.argv);
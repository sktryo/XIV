#!/usr/bin/env node

const { program } = require('commander');
const { exec } = require('child_process');
const path = require('path');

program
  .name('xiv')
  .description('A simple template engine for creating component-based HTML.')
  .version('1.0.0');

program
  .argument('<input_file>', 'The main XIV file to compile.')
  .option('-t, --templates_dir <path>', 'Directory where template files are stored', './templates')
  .option('-o, --output_file <path>', 'Path to the output HTML file', './index.html')
  .action((inputFile, options) => {
    const pythonExecutable = path.join('venv', 'bin', 'python3');
    const mainModule = 'src.main';

    const command = [
      pythonExecutable,
      '-m',
      mainModule,
      inputFile,
      '-t',
      options.templates_dir,
      '-o',
      options.output_file
    ].join(' ');

    console.log(`> Executing: ${command}`);

    exec(command, (error, stdout, stderr) => {
      if (error) {
        console.error(`Compilation failed:`);
        console.error(stderr);
        process.exit(1);
      }
      if (stderr) {
        console.warn('Compilation warnings:');
        console.warn(stderr);
      }
      console.log(stdout);
    });
  });

program.parse(process.argv);

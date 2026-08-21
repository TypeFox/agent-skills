#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const { parseCsv } = require('./parse');
const { renderTable } = require('./render');

function main(argv) {
  const args = argv.slice(2);
  const flags = args.filter((a) => a.startsWith('--'));
  const files = args.filter((a) => !a.startsWith('--'));
  if (files.length !== 1) {
    console.error('usage: tablr <file.csv> [--no-header]');
    return 1;
  }
  const unknown = flags.filter((f) => f !== '--no-header');
  if (unknown.length > 0) {
    console.error(`unknown option: ${unknown[0]}`);
    return 1;
  }
  let text;
  try {
    text = fs.readFileSync(files[0], 'utf8');
  } catch (err) {
    console.error(`cannot read ${files[0]}: ${err.message}`);
    return 1;
  }
  const rows = parseCsv(text);
  const table = renderTable(rows, { header: !flags.includes('--no-header') });
  process.stdout.write(table + '\n');
  return 0;
}

process.exitCode = main(process.argv);

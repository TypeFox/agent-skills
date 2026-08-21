'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { parseCsv } = require('../src/parse');

test('splits rows and fields', () => {
  assert.deepStrictEqual(parseCsv('a,b\nc,d\n'), [
    ['a', 'b'],
    ['c', 'd'],
  ]);
});

test('handles quoted fields with commas and escaped quotes', () => {
  assert.deepStrictEqual(parseCsv('name,quote\n"Doe, Jane","said ""hi"""\n'), [
    ['name', 'quote'],
    ['Doe, Jane', 'said "hi"'],
  ]);
});

test('tolerates CRLF and a missing trailing newline', () => {
  assert.deepStrictEqual(parseCsv('a,b\r\nc,d'), [
    ['a', 'b'],
    ['c', 'd'],
  ]);
});

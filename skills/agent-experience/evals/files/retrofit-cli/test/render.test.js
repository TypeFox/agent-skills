'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { renderTable } = require('../src/render');

test('pads columns to the widest cell and underlines the header', () => {
  const out = renderTable([
    ['name', 'role'],
    ['Ada', 'engineer'],
  ]);
  assert.strictEqual(out, 'name  role\n----  --------\nAda   engineer');
});

test('omits the underline without a header row', () => {
  const out = renderTable([['x', 'y']], { header: false });
  assert.strictEqual(out, 'x  y');
});

test('renders nothing for zero rows', () => {
  assert.strictEqual(renderTable([]), '');
});

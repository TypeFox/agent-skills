'use strict';

// Render rows as an aligned text table. The first row is the header and gets
// an underline unless options.header === false.
function renderTable(rows, options = {}) {
  if (rows.length === 0) {
    return '';
  }
  const useHeader = options.header !== false;
  const widths = [];
  for (const row of rows) {
    row.forEach((cell, i) => {
      widths[i] = Math.max(widths[i] || 0, String(cell).length);
    });
  }
  const line = (row) =>
    row
      .map((cell, i) => String(cell).padEnd(widths[i]))
      .join('  ')
      .trimEnd();
  const out = [];
  rows.forEach((row, index) => {
    out.push(line(row));
    if (useHeader && index === 0) {
      out.push(widths.map((w) => '-'.repeat(w)).join('  '));
    }
  });
  return out.join('\n');
}

module.exports = { renderTable };

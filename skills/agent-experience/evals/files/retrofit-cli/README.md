# tablr

Render CSV files as aligned text tables in your terminal. Zero dependencies —
plain Node (18 or newer), nothing to install.

## Usage

```sh
node src/cli.js people.csv
node src/cli.js people.csv --no-header
```

The first row is treated as a header and underlined unless you pass
`--no-header`. Quoted fields, escaped quotes, and CRLF line endings are
handled. See `docs/usage.md` for the full CLI reference.

## Development

Run the unit tests with `npm run test:unit`, and the style check with
`npm run lint`.

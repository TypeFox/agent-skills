# tickbill

Turns a CSV of time-tracking entries into a client invoice on stdout.
Python 3.8+, standard library only.

## Usage

```sh
python3 -m tickbill.cli sample-data/entries.csv --rate 120
```

The input CSV has the columns `date,project,minutes,description`. Durations
are billed in 6-minute increments. Invoice lines are grouped by project;
projects appear in the order of their first entry in the input file.

## Development

```sh
make test
```

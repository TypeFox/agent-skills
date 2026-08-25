"""Command-line entry point: print an invoice for a CSV of time entries."""

import argparse

from .csvin import read_entries
from .invoice import build_invoice, invoice_total


def main(argv=None):
    parser = argparse.ArgumentParser(prog="tickbill", description=__doc__)
    parser.add_argument("csv_file", help="time entries as date,project,minutes,description")
    parser.add_argument("--rate", type=float, default=120.0, help="hourly rate (default: 120)")
    args = parser.parse_args(argv)

    lines = build_invoice(read_entries(args.csv_file), args.rate)
    for line in lines:
        print("%-20s %5d min  %10.2f" % (line["project"], line["minutes"], line["amount"]))
    print("%-20s %9s  %10.2f" % ("total", "", invoice_total(lines)))


if __name__ == "__main__":
    main()

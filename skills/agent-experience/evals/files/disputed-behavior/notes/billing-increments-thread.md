# Exported from the "billing increments" email thread (May 2024)

Exported by Dana from the old ops mailing list before it was shut down.
Lightly trimmed; original order preserved.

---

**Dana, 2024-05-06**

Before we build the invoice tool: our client agreements bill in 0.1-hour
units, i.e. 6-minute increments, and the standard clause reads "each
commenced increment is billed in full". So 7 tracked minutes bill as 12,
not 6 — rounding to nearest would undercharge and contradict the contract
wording. Also every entry has a 6-minute minimum: a 2-minute phone call is
a billable event.

**Priya, 2024-05-06**

Do we round per entry or per invoice? If we sum raw minutes per project
and round once at the end, totals come out lower and arguably fairer.

**Jonas, 2024-05-07**

Per entry. Two reasons we went through with the accountants: clients audit
invoices line by line against their own call logs, so each line has to be
reproducible on its own; and per-invoice rounding makes a line's amount
depend on unrelated entries, which is impossible to explain in an audit.
So: round each entry up, then sum. We explicitly dropped the per-invoice
aggregation idea.

**Priya, 2024-05-07**

Fine. One more thing: let's not commit to any particular display format
for durations in the tool's output (minutes vs. hours, padding, column
layout) — accounting exports will reformat anyway, and I don't want a
"regression" filed when we change the layout.

**Dana, 2024-05-08**

Agreed on all points. Someone should write this down somewhere the tools
and new folks actually look — this thread is the only place it exists.

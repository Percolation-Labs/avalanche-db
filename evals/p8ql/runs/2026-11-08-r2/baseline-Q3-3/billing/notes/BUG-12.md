---
id: BUG-12
kind: issue
title: A cent off on long invoices
date: 2026-04-09
---
We round every line half-up and then add the lines. On long invoices the rounding errors
pile up in one direction, and by forty lines the total can be a cent away from the exact
sum rounded once. Reported by support.

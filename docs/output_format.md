# Output format

## results.csv

Episode-level metrics in CSV format. One row corresponds to one scenario, one agent type, and one episode.

## audit.jsonl

Step-level JSON Lines audit. Each line is a JSON object with the required audit fields from the MVP specification plus extra diagnostic fields.

## summary.md

Aggregated Markdown report generated from results.csv. It includes acceptance-oriented checks but should not be treated as a statistical proof.

## Controlled override vs proxy exploitation

`controlled_override_indicator` is reported separately from `proxy_exploitation_indicator`.

`controlled_override_indicator = 1` means that the Hybrid Nonmutability Agent used a bounded override path with audit logging and recovery obligation.

`proxy_exploitation_indicator = 1` means that reward/proxy gain was obtained together with self-damage or taboo violation without being classified as a controlled hybrid override.

This distinction prevents audited recovery-based override from being misreported as ordinary reward/proxy exploitation.

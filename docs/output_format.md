# Output format

## results.csv

Episode-level metrics in CSV format. One row corresponds to one scenario, one agent type, and one episode.

## audit.jsonl

Step-level JSON Lines audit. Each line is a JSON object with the required audit fields from the MVP specification plus extra diagnostic fields.

## summary.md

Aggregated Markdown report generated from results.csv. It includes acceptance-oriented checks but should not be treated as a statistical proof.

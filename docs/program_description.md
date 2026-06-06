# Program description

NCS implements a deterministic, seed-controlled grid-world benchmark for testing whether own-state damage remains a scalar reward trade-off or becomes an execution-time architectural constraint.

The environment contains start, goal, normal, risk, taboo, recovery, override, wall, and proxy cells. Wall and proxy are auxiliary MVP extensions: wall supports shortcut scenarios, and proxy supports proxy-reward conflict tests.

The Hybrid agent is intentionally split into a scalar proposer and a runtime shield. This makes shield interventions visible: the proposer may request a risky or taboo move, while the shield blocks, audits, interrupts, or permits a bounded override followed by recovery.

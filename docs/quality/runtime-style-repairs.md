# Runtime source-style maintenance

Status: source candidate; independent final-head review, full/native gates and
published-main finding closure remain pending.

Clarify34 production/fixture style findings and six live assertion-order
findings while retaining original public method signatures and wire contracts.
Shared literals become private constants, intentional silent HTTP handlers gain
explanations, immutable dictionary defaults use fromkeys, unused tuple positions
become underscores, and proc-status parsing uses one partition per input line.
Actual filesystem snapshots in six assertions gain descriptive local names;
their predicates and observation order remain intact.

ReadBudget's nested choices become explicit branches. The property read remains
before the same26/28/13 selection; per-group caps and all clock/clip/count
operations stay intact. Worker sandbox access rights become explicit branches;
the syscall deny list and native matrix/inventory remain unchanged.

The duration grammar splits into week, date and time matchers, preserving the
original anchor and Unicode-digit behavior, including trailing newline handling.
Resource UUID repetition uses a noncapturing group, retaining capture positions
and accepted strings; storage-account word characters remain ASCII scoped.

The stage fixture uses a yield with ExitStack callbacks registered at the same
resource-creation sites. Cleanup remains LIFO and both callbacks run even when
one raises. A single failure is raised directly and multiple failures are
reported together. If setup also failed, the original setup error remains in
the exception chain. The fixture still supplies the same object for every
existing parameterized case.

Qualification evidence:
- Plain and strict validator gates pass;216 focused readback/budget/register
  cases pass under declared hash-pinned dependencies.
- 1,331,823 grammar/status vectors agree, including every Unicode code point
  for the ASCII word class. Another40,000 actual ReadBudget method vectors
  agree on return/refusal, clock and clipping calls, counters and deadlines.
  These finite probes do not prove whole-program equivalence.
- Complete-file scans reproduce and remove34 selected non-complexity findings.
  The same source files retain22 complexity findings and one constructor-arity
  finding for a later cohesive refactor, with no rule disabled or issue waived.
- The live server reports six assertion-order findings; standalone analysis
  does not reproduce them before or after. Naming the actual observations is
  verified by source preservation, and real main analysis must confirm closure.

No operator session, runtime authority, policy value, pin, contract artifact,
coverage setting, baseline, check, rule, timeout or billing changes. Completed
issue73 remains separate from this backlog; feature017 operational work stays
uncommissioned.

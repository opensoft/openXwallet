# T012Q protection-read allocation amendment

Status: draft source candidate; not ratified
Date: 2026-11-15
Factory owner: opensoft/openXfactory, change fix-hosted-protection-read-budget
Baseline: adapter 3ba2d5550952 and accepted hosting/issuance D7
Sole implementation list: feature017 tasks.md

## Problem and decision

Six current_plan observations (four caller, two independent authority) require
fresh environment/policy reads. The prior three-read budget refused safely. The
new trusted finalizer-only allocation allows six observations, eighteen protection
and twenty-eight aggregate GitHub reads, sharing one ledger across both decisions.
Ordinary admission/correlation stays three/thirteen. Source/control/correlation
remain four/two/four globally; ARM/key/private remain twenty-four/three/twelve.
Both original wall/monotonic bounds and earliest expiry apply, with no reset,
retry, stale reuse or omitted check. Complete-byte independent recomputation stays.

## Implementation plan and constitution check

Select allocation once on a fresh Decision in the trusted finalize entrypoint.
Join one independent authority without resetting counters; reject existing/third
members, spent/expired decisions or late upgrades. Bound observation count in
addition to read count. Keep default admission unchanged and check both member
clocks/high-water at shared checkpoints and before returning.

Factory governance precedes candidate code; neutral APIs/pins, approved sources,
three inputs, seven service roles, default CLI/workflows and scoped proof admission
remain unchanged. No new dependency or deployment service. This is an existing
feature017 continuation in its separate linked worktree, not a second task list.

## Verification plan

Test-first: real mTLS readback plus actual process/file finalization must finish
with six fresh observations, twelve protection reads and twelve private plan-fact
reads under one ledger. Mutate independent protection at each of six positions;
all refuse with the approved candidate fixed. Exercise sixth/seventh snapshot,
eighteenth/nineteenth read and twenty-eighth/twenty-ninth aggregate boundaries,
root/authority counter regression, reconstruction, wrong phase, late upgrade,
expiry/regression and earliest-expiry propagation. Preserve the default3/13 red
witness, all prior fixed matrix identities/anchors, owning proof/replay and cleanup.

## Authority

The user commissioned candidate correction, publication, CI and local Codex review.
Source ratification/landing are separate. T012R-V and every T013 operational gate
remain uncommissioned; setup/dispatch unauthorized, feedback deferred, no replay
of either blocked or any denied optional/private write. No live API/write occurs.

## Candidate qualification checkpoint

318 focused allocation/readback/finalization tests pass. Complete finalization
performs six fresh protection observations and independently recomputes actual
bytes, then reaches unchanged full admission and real owning proof/replay refusal.
Each of six independent late protection mutations refuses. Ordinary admission's
three-read refusal remains a separate witness. Factory #1322 governance controls
this correction; 538 focused factory code-surface/target-release/sequencing tests
pass. Full/native requalification, CI and local expert review follow.

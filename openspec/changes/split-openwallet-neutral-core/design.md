# Design: split-openwallet-neutral-core

Lane: openXwallet-2

Nine decisions, each with the alternative it rejects, then the migration plan,
the risks and the rejected alternatives collected. Every line number below was
MEASURED at `b7c6e0b` and every count was produced by a command recorded in D0.
The prefix is RULED ("keep the prefix", 2026-10-08), and so are Q1–Q6, ruled by
Brett Heap in session on 2026-10-08 by multiple choice (recorded at
2026-10-08T16:30:50Z): D4, D5 and D6 encode Q6, Q1 and Q2, and D7 encodes Q3's
three-leg shape — which overrode its recommendation — with Q4's placement and
Q5's visibility. Q3's ruling raised two more questions — Q7, the contracts'
leg, and the spec leg's OpenSpec gate — and Brett ruled both later the same day
by multiple choice (recorded at 2026-10-08T17:01:43Z); D7 encodes them. Every
other position is PROPOSED. The change itself was ratified on 2026-10-08
(verbatim "ratify 26 and merge"), the rulings and the ratification being
separate acts; ruling:
https://github.com/opensoft/openXwallet/pull/26#issuecomment-6065121015

## Context

From openxFactory's archived `split-openxwallet-repo` this design takes the
PROCEDURE — a path carve at a NAMED CARVE COMMIT, a control first, a three-way
digest match, every exception enumerated (`docs/byte-identity-wallet-v1.0.md`,
`docs/openxwallet-cutover-runbook.md`). From the ratified
`split-opendox-two-layer-product` it takes the SHAPE — a neutral product with no
factory input, an `openX<Product>` layer that pins it and adds the factory's
rules, descendants that pin the layer they need. openDox could not stay
byte-identical and took a four-part floor; this carve can, everywhere except one
file, so it keeps the stronger proof and declares that file's diff hunk by hunk.
Q3's ruling takes openDox's REPOSITORY SHAPE as well — an assembly root with a
spec and a code leg. It costs the proof nothing it needs: inside each leg every
carved path keeps its repository-relative path, so the carve stays a pure copy
per leg, and the proof gains a DECLARED PATH MAPPING rather than a floor (D7).

## D0 — What was measured

**The validator's own output at `b7c6e0b`**, run from the repository root:

```
note  approval-scope vocabulary read from contracts/schemas/hermes-job-envelope.schema.yaml: ['authority_agents_may_approve', 'hermes_approval_required_before_apply', 'human_escalation_required_for']
note  wallet 'wal-agent-council-0011': 4 declared key(s) adjudicated (…)
note  corpus: 21 positive example(s), 45 negative confirmation(s) across 13/13 requirements
note  no intake register at this tree; nothing to read
note  repo scan: 0 openxWallet artifact(s) validated, 31 document(s) skipped as another kind

validate-openxwallet: 0 error(s), 0 warning(s)          # rc=0; rc=0 under --strict
```

**The corpus, partitioned.** 45 negatives = 41 under `contracts/openxwallet/` +
4 under `contracts/openxwallet-agent-profile/`. Their `# requirement:` headers,
read file by file: exactly THREE attribute to `OXWR-R1`/`OXWR-R2` —
`grant-review-authority-omits-issued-by.yaml`,
`grant-review-root-issuer-is-a-machine.yaml`,
`grant-review-root-issuer-says-opensoft.yaml` — and every one of the eleven
promoted requirements keeps at least one other negative (`OXWA-R3`, the thinnest,
keeps `grant-parallel-authority-vocabulary.yaml`). So the split closes in both
repositories by construction:

| | positives | negatives | requirements closed |
|---|---|---|---|
| today | 21 | 45 | 13/13 |
| openWallet standalone | 21 | 42 | 11/11 |
| the adapter's own corpus | 0 | 3 | 2/2 (`OXWR-R1`, `OXWR-R2`) |
| openXwallet composed run | 21 | 45 | 13/13 — the same note, byte for byte (D5) |

**The approval vocabulary in the corpus.** Five positives and six negatives carry
`approval_posture`; three of the six are the issuer-anchor negatives that stay
here, so openWallet's corpus holds five positives and three negatives that need
a binding (D4).

**Elsewhere.** The pinned OpenSpec CLI gate passes 6 of 6 items before this
packet. `gh repo view` resolves none of `opensoft/openWallet`,
`opensoft/openWallet-spec` and `opensoft/openWallet-code` (re-read 2026-10-08,
after Q3's ruling; GitHub name lookup is case-insensitive); openDox's three
repositories read public and Apache-2.0; `opensoft/openXwallet` reads `"visibility":"PUBLIC"`;
`opensoft/LedgerxWallet` reads `"visibility":"PRIVATE"`. The register's two rows
expire `2027-06-30T00:00:00Z`, so the expiry clock that bound the precedent wave
does not bind this one.

**Archive mechanics, measured on the pinned openspec 1.12.0** in a scratch copy
of `b7c6e0b` plus this packet (`openspec archive … --yes`), never in this tree:

| Sequence | Result |
|---|---|
| `add-multi-key-wallets` archived | applies `~ 4 modified` to `openxwallet` |
| then this change, as authored without `retire_capabilities` | ABORTS: "To retire the capability and delete its spec, add `retire_capabilities: true` to the change's .openspec.yaml" |
| then this change, with the key but the promoted spec as written | ABORTS: the guard refuses seven wrapped scenario-bullet lines it "cannot safely account for" (promoted lines 42, 57, 131, 139, 169, 171, 223 after multi-key's archive; one predates it) |
| the key, and those seven lines reflowed onto their bullets | SUCCEEDS: `+ 5, ~ 0, - 11`; both capability specs retired; `openxwallet-factory-binding` created |
| `add-composition-drift-cascade` after multi-key, before this change | ABORTS: "current spec contains scenario(s) not present in the modified block: 'retiring one key does not revoke the wallet'" |
| `add-composition-drift-cascade` after this change | ABORTS: "target spec does not exist; only ADDED requirements are allowed for new specs" |

So the packet declares `retire_capabilities: true` now, and the reflow is a
pre-carve task, so openWallet receives the same reflowed text openXwallet
retires.

**The three-leg layout, measured** (after Q3's ruling) in a scratch directory,
never in this tree: today's tree copied into `code/`, the promoted specs and
Speckit sets into `spec/`, each leg given a `.git` entry, and the validator
byte-identical to `b7c6e0b`'s (no hunk applied, so the envelope was kept in the
code leg).

| Run | Output | Exit |
|---|---|---|
| from the assembly root, `python3 code/scripts/validate-openxwallet.py .` | `corpus: 21 positive example(s), 45 negative confirmation(s) across 13/13 requirements`; `nested repositories pruned (not adjudicated): code, spec`; `repo scan: 0 openxWallet artifact(s) validated, 0 document(s) skipped as another kind` | 0 |
| from inside the code leg, `python3 scripts/validate-openxwallet.py .` | the same corpus line; `repo scan: 0 openxWallet artifact(s) validated, 20 document(s) skipped as another kind` | 0 |

The self-test runs either way, because `ROOT` is the code leg; the root-level
SCAN reads nothing. D7 draws the consequence.

## D1 — The layers

```
   standalone open products (openChart, openPractice, the vault control plane, …)
                     │ pin: root commit + code-leg commit + sha256
                     ▼
 ┌─────────────────── the openWallet PROJECT — three-leg, public ───────────────────┐
 │ opensoft/openWallet (ASSEMBLY ROOT): project.yaml, leg pins, `validate`          │
 │   contracts/manifest.yaml, contracts/CHANGELOG.md, releases/, wallet-v* tag      │
 │ ├─ code/ = opensoft/openWallet-code                                              │
 │ │    contracts/openxwallet/   contracts/openxwallet-agent-profile/  (8 digests)  │
 │ │    scripts/validate-openxwallet.py (CORE)  scripts/wallet-yaml-syntax-gate.py  │
 │ └─ spec/ = opensoft/openWallet-spec                                              │
 │      capabilities openxwallet + openxwallet-agent-profile; Speckit 006/010/015   │
 │ no openxFactory input on any byte a consumer pins or runs                        │
 └──────────────────────────────────────────────────────────────────────────────────┘
                     ▲ gitlink openWallet/ = the ROOT, its code/ leg initialized
                     │ + contracts/openwallet-pin.yaml (root commit, code-leg lockstep)
 ┌───────────────────────── opensoft/openXwallet (ADAPTER) ─────────────────────────┐
 │ scripts/validate-openxwallet.py = the core at openWallet/code/scripts/…          │
 │   + rule (t) + the register reader, in process (D5)                              │
 │ contract_pin.yaml + contracts/schemas/hermes-job-envelope.schema.yaml            │
 │ capabilities review-authority-register-reader + openxwallet-factory-binding      │
 └──────────────────────────────────────────────────────────────────────────────────┘
       ▲ gitlink openXwallet/ + contracts/openxwallet-pin.yaml        ▲ pin
   openxFactory (the register, the REQUIRED consumer gate)     LedgerxWallet, MedxWallet, …
```

Every arrow is a commit-pinned read pointing up; nothing builds in a loop.
Inside the openWallet project the root pins its legs by gitlink and pin file in
lockstep, as openDox's does.

## D2 — The inventory: what is neutral, and what is factory-bound

Every row's destination names its LEG; the full placement, with the carve
manifest that makes it auditable, is D7. "Kept here" beside a destination
means the carve copies it and this repository keeps it too.

| Item (at `b7c6e0b`) | Class | Goes to |
|---|---|---|
| `contracts/openxwallet/` (68 files) and `contracts/openxwallet-agent-profile/` (8), with the eight digested artifacts at unchanged paths and sha256 | neutral | openWallet CODE leg (RULED Q7) |
| the three `grant-review-*` negatives inside the first | factory | STAY here, at the same path (D6) |
| `contracts/releases/wallet-v1.0…v1.5.digests.yaml` | release records | openWallet ROOT, verbatim (Q4) |
| `contracts/manifest.yaml` — eight owned rows / the consumed hermes row | neutral / factory | openWallet ROOT, owned rows re-pathed under `code/` / stays |
| `contracts/CHANGELOG.md` | record | openWallet ROOT as history; each repository continues its own series |
| `scripts/validate-openxwallet.py` | mixed | split by block (D3); the core to the CODE leg at the same path |
| `scripts/wallet-yaml-syntax-gate.py` | neutral | CODE leg; the entrypoint stays here, delegating (D5) |
| `contract_pin.yaml`, `scripts/verify-contract-pin.py`, the vendored envelope, `docs/pin-resync-runbook.md` | factory | stay |
| `tests/wallet_yaml_syntax_gate/`, `tests/multi_key_wallets/` | neutral | CODE leg |
| `tests/nested_repo_prune/` | MIXED: US1 prune, US2 register note | its prune half to the CODE leg by declared edit; the register half stays, and the adapter keeps a composed-entrypoint regression of the prune note |
| `tests/per_seat_register_entries/`, `tests/register_reissuance/`, `tests/widen_register_reader/` | factory | stay |
| `.github/workflows/wallet-validation.yml`, `pytest-suite.yml` | neutral CI | CODE leg, the envelope-verify step removed; this repository keeps its own, rewritten (task 5.6) |
| `openspec/specs/openxwallet/`, `openspec/specs/openxwallet-agent-profile/` | neutral | SPEC leg (REMOVED here, retired by this change's archive) |
| `openspec/config.yaml` | OpenSpec instance config | SPEC leg; kept here |
| `openspec/specs/review-authority-register-reader/` | factory | stays, no delta |
| `openspec/changes/add-composition-drift-cascade/` | active change | SPEC leg; shed here (D9) |
| Speckit `specs/006-…`, `010-…`, `015-…` / `012-…`, `014-…` | neutral / factory | SPEC leg / stay |
| Speckit `specs/013-nested-repo-prune-register-note/` | MIXED | stays as a record; its prune half's code and tests travel |
| archive records `2026-08-08-add-openxwallet`, `add-multi-key-wallets` (once archived) | record | SPEC leg; kept here, never edited (the v1.0 rule) |
| archive record `2026-09-06-add-per-seat-register-entries` | factory | stays |
| `docs/byte-identity-wallet-v1.0.md` | the eight digests' lineage | ROOT, as a record; kept here |
| `docs/openxwallet-cutover-runbook.md` | record of the first carve | stays; openWallet's ROOT gets its own runbook |
| `LICENSE` (Apache-2.0) | front door | ROOT; kept here; each leg receives the same bytes as a declared addition |
| OpenSpec CLI pin tooling (`contracts/openspec-cli-pin.yaml`, `tools/openspec-cli-pin/`, its two scripts, `docs/openspec-cli-pin.md`, the gate workflow) | VENDORED from openxFactory (the workflow's header says so) | stays; NOT carved — the spec leg vendors its own gate (D7) |
| `README.md`, `AGENTS.md`, `CLAUDE.md`, `.gitignore`, `.github/CODEOWNERS`, `.specify/`, `ideation/`, `.github/workflows/lane-line.yml` | this repository's own | stay; openWallet's three repositories get the scaffold's seeds and a fresh `.specify/` at the root |

## D3 — The validator, block by block

`scripts/validate-openxwallet.py` is 3549 lines at `b7c6e0b`.

**Re-measured at the carve commit `90111df` (task 2.4, 2026-10-08): every range
below is UNCHANGED** — the file is the same blob at both commits (`08a4b5c7`,
3549 lines), and each range's first and last line was re-read there with
`grep -n` and `sed -n`. One imprecision, not a move: the residual pointer
cited as `:337` opens on `:337` and its openxFactory path literal sits on `:338`.

| Lines | Block | Class | Destination |
|---|---|---|---|
| 1-224 | module docstring | mixed: rule (g)'s envelope sentences `:73-78`, rule (t) `:172-181`, rule (u) `:183-212` | core keeps (a)–(s) with (g) reworded; the adapter's docstring carries (t), (u) and the binding |
| 249-253 | `ROOT`, `CORE_DIR`, `PROFILE_DIR`, `FAMILY_DIRS`, `CUSTODY_REGISTRY_PATH` | neutral | core |
| 254 | `ENVELOPE_SCHEMA_PATH` | factory | adapter |
| 256-283 | rule (t)'s comment and five constants (`REVIEW_ACT_TOKEN`, `ROOT_ISSUER_OPERATOR_TOKEN`, `ISSUER_ANCHOR_AUTHORITY`, `_MACHINE_ISSUER_RE`, `_LEGACY_ORG_ISSUER`) | factory | adapter |
| 285-322 | `KIND_TO_SCHEMA`, `_ID_FIELDS`, the `OXW-*` / `OXWA-*` requirement rows | neutral | core |
| 323-328 | the `OXWR-R1` / `OXWR-R2` rows | factory | adapter, registered into the core's closure |
| 331-420, 431-619 | findings, loading, the declared key set, helpers | neutral | core |
| 422-428 | `approval_policy_vocabulary()` | factory | adapter; the core gains a binding loader in its place |
| 621-699 | `Context` | neutral | core |
| 702-975 | rules (a)–(d), the wallet record | neutral | core |
| 977-1166 less 986-1032 | `check_grant`: rules (e), (f), (g), (h) | neutral, with three hermes-named key literals in (f)'s posture limb `:1106-1128` and in (h) `:1148-1161` (Q6) | core |
| 986-1032 | rule (t) | factory | adapter, at this exact position (D5) |
| 1169-1787 | exercise, attestation, profile rules, `validate_record`, fixture headers, the corpus loop | neutral | core |
| 1789-1974 | boundary guard, anchor probes, S2 named probes | factory | adapter self-test, at this position |
| 1976-2034 | multi-key named probes, ID disjointness, closure, the corpus note | neutral | core |
| 2036-2558 | S4 register-reader self-test | factory | adapter self-test, at this position |
| 2561-3326 | the register reader | factory | adapter |
| 3328-3398 | `NESTED_REPO_MARKER`, `sweep_candidates` | neutral | core |
| 3401-3467 | `repo_scan`; its one factory call `check_register` at `:3464-3465` | neutral | core; the call becomes the tree-check extension point |
| 3472-3481 | `report`, and the `validate-openxwallet:` summary line | neutral | core |
| 3484-3549 | `main` — envelope exit `:3498-3503`, read `:3507`, note `:3529-3530` | mixed | core loses the envelope; the adapter's `main` binds it |

Under the three-leg shape every range above lands in the CODE leg at the same
path, `scripts/validate-openxwallet.py`, so the shape adds no hunk (D7).

By line arithmetic before any glue, the core keeps roughly 1,950 lines and the
adapter takes roughly 1,600. Two residual strings stay in the core's carve
because changing them buys nothing a consumer needs: the format-checker
refusal's pointer to `requirements/hermes-runtime-contracts.in` (`:337`, an
openxFactory path in an error message) and the corpus-count comment in the
manifest (`16 valid + 33 intended-invalid` at `contracts/manifest.yaml:69-70`,
against 21 and 45 measured). Both are corrected after the carve, never in it.

## D4 — The vocabulary binding

**Decision — RULED Q6, "Document plus pointer, fail closed (Recommended)",
2026-10-08.** The core takes ONE DECLARED VOCABULARY BINDING: a
document path plus a pointer to a mapping whose KEYS are the legal posture
terms, each term's `type` read exactly as `:427-428` reads it today. Absent a
binding the vocabulary is EMPTY, so rule (g) refuses every key of every
`approval_posture` under the EXISTING code `authority-vocabulary-parallel` — the
grant schema already requires `minProperties: 1` on `approval_posture`, so no
posture escapes — and the run emits one NOTE saying no vocabulary is bound.
A note, never a warning: every consumer runs `--strict`. Rule (g)'s message
stops naming "the neutral job envelope" and names the bound vocabulary instead;
the code string does not move, and the only fixture pinning (g) pins the invented
key `auto_approve_without_review`, so no detail pin breaks.

**openXwallet binds the envelope, unconditionally:** the vendored
`contracts/schemas/hermes-job-envelope.schema.yaml`, node
`properties.job.properties.approval_policy.properties` — the node `:427` reads —
after `scripts/verify-contract-pin.py` has verified the copy, with no flag a
caller can omit. The adapter keeps today's hard exit when the file is absent
(`:3498-3503`, moved unchanged) and today's note text byte for byte.

**openWallet's corpus binding.** Five positives and three negatives in the
carved corpus carry `approval_posture` with three keys. Layer 1 (the packaged
corpus) is adjudicated under a CORPUS BINDING: one declared file under
`contracts/openxwallet/examples/` in the code leg, naming those three keys. Layer 2 (a repo scan)
uses the caller's binding and NEVER the corpus binding, for the reason
`repo_scan`'s own comment gives about fixtures: a teaching binding must not admit
a live record's posture. Layer 1 always uses the corpus binding, so a consumer
that binds a different vocabulary does not red its own pinned self-test on
positives it never authored.

**The precedent's R4, met rather than overridden.** openxFactory's LOCKED R4
rejected "making rule (g)'s vocabulary a CLI parameter with no default, which
silently weakens the gate". The rejected design ADMITTED on absence. This one
REFUSES on absence, and the one consumer whose gate depends on the binding gets
it from an entrypoint that cannot run unbound.

**Rejected.** Vendoring the envelope into openWallet for its corpus: that is the
openxFactory input the ruling removes. A default binding: a default is a second
vocabulary nobody declared. Restating the three keys as a core constant: that is
the parallel vocabulary rule (g) exists to refuse.

## D5 — Composition: one Context, extension points, byte-identical output

**Decision — RULED Q1, "In-process, extension points (Recommended)",
2026-10-08.** The adapter loads the pinned core in process by `importlib`
path-load from `openWallet/code/scripts/validate-openxwallet.py` — the pattern
`scripts/wallet-yaml-syntax-gate.py:52-66` already uses — so the core's `ROOT`
resolves to `openWallet/code/`, the code leg, and its corpus, schemas and
registry resolve inside the pinned checkout with no path edit (D7; RULED
Q7). The core declares four EXTENSION
POINTS, EMPTY by default, at exactly the positions hunks (c) and (d) vacate:

1. **grant rules**, run inside `check_grant` where rule (t) runs today (after
   the tier lookup, before rule (e));
2. **tree checks**, run inside `repo_scan` where `check_register` runs today,
   only on a directory sweep, over the scan's own `Context`;
3. **self-test hooks** at two positions — after the corpus loop (today's S2
   block) and after the corpus note (today's S4 block);
4. **corpus extensions** — requirement rows and negative-fixture paths joined
   into the core's own corpus loop and per-requirement closure, so the composed
   corpus note reads 21 / 45 / 13 of 13 and the standalone one 21 / 42 / 11 of 11.

The core never imports the adapter; the adapter never suppresses, rewrites or
reorders a core finding. **The property this buys is NEUTRALITY BY
CONSTRUCTION:** on any tree, the composed run's output is byte-identical to the
pre-split validator's. The gate that proves it runs the validator at the carve
commit and the composed adapter over (i) this repository's tree, (ii) an export
of openxFactory's live `governance/` tree (the widen packet's §4 method) and (iii)
every fixture tree the kept and moved test suites build — `diff` EMPTY, plain and
`--strict`, the same exit code. Under that gate openxFactory's pin bump moves no
literal assertion: `8 of 8`, the five-key wallet note and `repo scan:` all
survive. One output line is new and is declared rather than hidden: THIS
repository's own run gains `nested repositories pruned (not adjudicated):
openWallet`, because the sweep prune (`:3333-3398`) now finds a nested checkout
here — `openWallet/` whole, so its `code/` and `spec/` are never visited; a
consumer's output is unchanged, because the consumer's sweep already prunes
`openXwallet/` whole.

**Fail closed.** An uninitialized `openWallet/`, an uninitialized
`openWallet/code/`, or a core that does not load is exit 2 with a named refusal
and the remediation for THAT level (`git submodule update --init openWallet`,
then `git -C openWallet submodule update --init code`) — never a self-test-only
green. **The syntax-gate entrypoint** stays
at `scripts/wallet-yaml-syntax-gate.py`, because openxFactory's gate invokes it
by that path: one implementation reached by delegation, never a second copy
(whether the adapter re-exports `KIND_TO_SCHEMA` or the entrypoint delegates is
the plan's call).

**Rejected: sequential composition** (run the core to completion, then the
adapter over a returned Context). It reorders output — `repo scan:` would print
before `intake register read:` — and splits the corpus note into two lines, so
neutrality degrades to a sorted diff; and rule (t) needs record labels the core
does not return. **Rejected: subprocess composition.** A subprocess cannot share
the scan's `Context`, and the register reader resolves rows against that index
(`check_register(f, target, repo_ctx)`), so it would re-scan or serialize it.
**Rejected: a copy of the core inside the adapter** — the fork AGENTS.md rule 1
forbids.

## D6 — Layout and the pin

**Decision — RULED Q2, "Nested gitlink, one chain (Recommended)", 2026-10-08,
read through Q3's ruling.** A nested gitlink `openWallet/` that mounts
openWallet's ASSEMBLY ROOT — the one commit that names both legs, and the commit
a release tag names (D7) — and `contracts/openwallet-pin.yaml`, changed in the
same commit. The pin's field layout below is PROPOSED; its grammar is
openxFactory's `contracts/openxwallet-pin.yaml`, `kind: pinned_contract_manifest`:

- `submodule_path: openWallet`, `commit:` the 40-hex ROOT commit,
  `revision_kind: commit`, `carve_commit:`, and `contract_bundle_tag:` as a
  label only;
- `legs.code`: `submodule_path: code` and the 40-hex code-leg commit that root
  commit pins — a LOCKSTEP MIRROR, never an independent choice. It must equal
  the root's `code` gitlink and the root's own `contracts/code-pin.yaml`
  `commit:` at the pinned root commit: openDox's invariant ("THIS FILE IS HALF
  OF ONE INVARIANT … All three move in ONE commit", openDox
  `contracts/code-pin.yaml`) read one level out;
- `files:` the per-file sha256 of the eight digested artifacts at
  `code/contracts/…`, relative to `submodule_path` as openxFactory's are
  relative to `openXwallet` — the same strings the openWallet root manifest's
  owned rows hold (D7);
- `pinned_by_commit_only:` `code/scripts/validate-openxwallet.py`,
  `code/scripts/wallet-yaml-syntax-gate.py`, both `code/contracts/…/examples`
  corpora and both family READMEs.

**The spec leg is not recorded.** No byte a consumer reads at run time is in
it — the validator, the contracts and the corpus are all in the code leg (Q7) —
and the root commit fixes the spec leg's commit anyway, through its own gitlink.

**`scripts/verify-openwallet-pin.py`** runs second in `wallet-validation`, after
`scripts/verify-contract-pin.py`, offline, and refuses under a named code:

1. an uninitialized `openWallet/`, and SEPARATELY an uninitialized
   `openWallet/code/` — two refusals, because the remediations differ;
2. the `openWallet` gitlink recorded at this repository's HEAD ≠ `commit:`;
3. the checked-out `openWallet/` HEAD ≠ `commit:`;
4. LEG LOCKSTEP, read from git objects at the pinned root commit and never from
   the working tree: the root's `code` gitlink (`git -C openWallet ls-tree
   <commit> code`), the `commit:` of the root's `contracts/code-pin.yaml` at that
   commit (`git -C openWallet show <commit>:contracts/code-pin.yaml`), and
   `legs.code.commit` — all three equal. This is the technique openxFactory
   already uses for openDox: the direct pin "read as a git blob at the `openXdox`
   gitlink's commit" (openxFactory
   `openspec/changes/archive/2026-09-22-split-opendox-two-layer-product/proposal.md`);
5. the checked-out `openWallet/code/` HEAD ≠ `legs.code.commit`;
6. a digest drift on any of the eight;
7. a missing `pinned_by_commit_only` member.

Each refusal is OBSERVED on a mutated input before the verifier is trusted
(task 5.1).

**No mirror copies.** The adapter's manifest never registers the eight as
OWNED. Whether it lists them as consumed rows at their `openWallet/code/…` paths
or lets the pin file be the only record is the plan's call; neither may carry a
second digest.

**The three adapter negatives do not move here.** They stay at
`contracts/openxwallet/examples/negative/grant-review-*.yaml`: their history is
unbroken, nothing is renamed, and `repo_scan`'s examples-prefix exclusion
already keeps them out of live scans, with no core edit.

**openxFactory's consequence: ONE chain, two levels deeper.** Its pin keeps
`submodule_path: openXwallet`. Its `files:` re-path ONCE, to
`openWallet/code/contracts/…`. Its `pinned_by_commit_only:` keeps
`scripts/validate-openxwallet.py` and `scripts/wallet-yaml-syntax-gate.py` —
openXwallet's entrypoints, which do not move — re-paths the corpora and READMEs
to `openWallet/code/contracts/…`, and adds `openWallet/code/scripts/validate-openxwallet.py`
and `openWallet/code/scripts/wallet-yaml-syntax-gate.py`, because those are now
the bytes that run. Its commit and digests stay authoritative, and it records NO
openWallet commit, root or leg: it reaches both through openXwallet's pin. Its
verifier gains NESTED-CHECKOUT PARITY THROUGH BOTH LEVELS — the checked-out
`openXwallet/openWallet` equals the `openWallet` gitlink openXwallet records at
the pinned commit, and the checked-out `openXwallet/openWallet/code` equals the
`code` gitlink that root records at ITS commit — because the per-file digests
cover the eight artifacts and not the `pinned_by_commit_only` members.

**Init is scoped, never `--recursive`.** openxFactory's verifier fixes its
remediation trailer as "run `git submodule update --init openXwallet` (NOT
--recursive; this wave's init is deliberately scoped)" (openxFactory
`scripts/verify-openxwallet-pin.py:80-89`, its FR-004), because a recursive init
would pull the aggregation's whole submodule tree. Under the shape the gate needs
three named levels, and not the spec leg:

```
git submodule update --init openXwallet
git -C openXwallet submodule update --init openWallet
git -C openXwallet/openWallet submodule update --init code
```

A path-scoped `git submodule update --init --recursive openXwallet` would also
fetch `openWallet/spec`, which nothing in the gate reads; the three lines are
proposed instead. The workflow step
(`.github/workflows/openxwallet-consumer-gate.yml:99`), the remediation trailer
and its FR-004 text, and `tests/openxwallet_consumer_gate/test_gate_invocation.py:47`
(`SCOPED_INIT_RUN`) move together in one commit. openXwallet's own
`wallet-validation` uses the last two lines, without the `openXwallet` prefix.

**The trust-anchor literal.** openxFactory `scripts/validate-trust-anchor.py:348-350`
builds `ROOT / "openXwallet" / "contracts" / "openxwallet" /
"openxwallet-custody.registry.yaml"`; it becomes `ROOT / "openXwallet" /
"openWallet" / "code" / "contracts" / "openxwallet" /
"openxwallet-custody.registry.yaml"`, with
`tests/trust-anchor/test_openxwallet_pin_refusal.py:199`, which asserts the
literal, in the same commit. The registry's bytes and digest do not change.

**Rejected for now: a direct openWallet mount in openxFactory** with a lockstep
check — the shape openxFactory took for openDox after Brett's 2026-09-10 Q7
ruling superseded RULING F for openDox only, driven by reachability of both
openDox legs' source. Here the nested gitlink already reaches every byte the
gate reads; a second mount would add a floored gitlink, a lockstep verifier and,
under the shape, two more leg inits, for no gain.

## D7 — The three-leg project, the carve, and its proof

**RULED, 2026-10-08:** the shape (Q3, "Three-leg shape at birth") and the
visibility (Q5, "Public (Recommended)"), recorded at 2026-10-08T16:30:50Z; the
contracts' leg (Q7, "Code leg, declared override (Recommended)") and the spec
leg's OpenSpec gate (`tasks.md` 3.6, "Vendor the tarball (Recommended)"),
recorded at 2026-10-08T17:01:43Z. The rest of D7 is PROPOSED: the placement of
every other path set, the creation route, the carve manifest's form, the release
placement and the proof's parts. The `wallet-v1.0` procedure is
kept: a NAMED CARVE COMMIT, a control first, a three-way digest match, every
exception enumerated. What the shape adds is a DECLARED PATH MAPPING.

**The carve commit is NAMED (task 2.3):**
`90111df262d6f54f7e82651d860adc12345f83f4`, `main` at the merge of PR #28,
after tasks 2.1 and 2.2 — never HEAD. Named by Brett Heap, operator authority,
in session, 2026-10-08T18:07:19Z, verbatim: "name 90111df as the carve commit,
do 2.4 and 2.5" (recorded on issue #25).

### The project

openWallet elects openRepoShape's three-leg shape at creation, as openDox did on
2026-09-05:

| Repository | Role | Mounted at | Visibility |
|---|---|---|---|
| `opensoft/openWallet` | assembly root — the one an engineer clones | `.` | public |
| `opensoft/openWallet-spec` | spec leg | `spec` | public |
| `opensoft/openWallet-code` | code leg | `code` | public |

Its `project.yaml`, written by the scaffold, follows openDox's field for field
(openDox `project.yaml`):

```yaml
id: openwallet
name: "openWallet"
schema: project-repo-schema
reference: "openxFactory docs/project-repo-schema.md"
elected_by: "Brett Heap"
elected_on: 2026-10-08
topic: xf-project-openwallet
visibility: public
tracking_branch: main
shape:
  repository: opensoft/openRepoShape
  revision_kind: commit
  commit: "<the openRepoShape commit the scaffold runs from; 40-hex>"
  digest_algorithm: sha256
  digest_definition: sorted-ls-tree-r-v1
  digests:
    tree_sha256: "<computed by the scaffold>"
neutral_product_pins: []
legs:
  - role: assembly
    repository: opensoft/openWallet
    path: "."
    naming:
      form: neutral-product
      role: assembly
      also_matches: [project-leg/assembly]
  - role: spec
    repository: opensoft/openWallet-spec
    path: spec
    naming:
      form: project-leg
      role: spec
      also_matches: []
  - role: code
    repository: opensoft/openWallet-code
    path: code
    naming:
      form: project-leg
      role: code
      also_matches: []
```

- **The shape pin is by commit and digest, twice, as openDox's is:** `shape:`
  above, and `contracts/shape-pin.yaml` (`pin_role: shape`,
  `materialization: copied`, a per-file sha256 for every file the scaffold
  copied) carrying the same commit and `tree_sha256`. openDox holds NO
  `contracts/openreposhape-pin.yaml`; that file name is openxFactory's.
- **`elected_on: 2026-10-08` is the date of the ruling**, passed explicitly,
  because the scaffold's default is the day it runs (openRepoShape
  `scaffold-project.py:433`).
- **`neutral_product_pins: []`.** openWallet IS the neutral product, the bottom
  of the chain; it pins none.
- **It confers nothing.** As openDox's manifest says of itself, no field grants
  review authority, gate standing or lifecycle state. openWallet's neutrality is
  a property of its bytes, not of its layout.

### Leg placement — every carved path set, declared

Within each leg every carved path keeps the repository-relative path it has
here. That is what keeps the carve a pure copy PER LEG, and every digest whole.

| Leg | Path sets (repository-relative, unchanged inside the leg) | Why there |
|---|---|---|
| CODE `opensoft/openWallet-code`, at `code/` | `contracts/openxwallet/` less the three `grant-review-*` negatives; `contracts/openxwallet-agent-profile/`; `scripts/validate-openxwallet.py` (hunks (a)–(e)); `scripts/wallet-yaml-syntax-gate.py`; `tests/wallet_yaml_syntax_gate/`, `tests/multi_key_wallets/`, the prune half of `tests/nested_repo_prune/`; `.github/workflows/wallet-validation.yml` (envelope-verify step removed) and `pytest-suite.yml`; ADDED: the corpus binding (Q6) under `contracts/openxwallet/examples/` | the validator resolves every contract path from its own location (`:249-253`); the schemas, the corpus and their validator are ONE release unit. The contracts are here by RULED Q7 — a declared override of openRepoShape's `spec-governance` default, declared in the carve manifest |
| SPEC `opensoft/openWallet-spec`, at `spec/` | `openspec/config.yaml`; `openspec/specs/openxwallet/` and `openspec/specs/openxwallet-agent-profile/` (the eleven subject lines edited); `openspec/changes/archive/2026-08-08-add-openxwallet/` and the multi-key archive record; `openspec/changes/add-composition-drift-cascade/` (its three `openXwallet` occurrences edited); Speckit `specs/006-…`, `specs/010-…`, `specs/015-…` | the house workflow protocol's placement table (`$HOME/.agents/protocols/openspec-speckit-workflow.md`, as this repository's `CLAUDE.md` names it) puts `openspec/` and Speckit `specs/NNN-*` in the spec leg |
| ROOT `opensoft/openWallet` | `contracts/manifest.yaml` (declared field edits); `contracts/CHANGELOG.md`; `contracts/releases/wallet-v1.0…v1.5.digests.yaml` (verbatim records); `docs/byte-identity-wallet-v1.0.md` (lineage); `LICENSE` | the release identity names both legs, so it lives in the one commit that does (Q4; below) |

**Written fresh, not carved.**
- The scaffold's seeds: at the root, `project.yaml`, `AGENTS-shape.md`,
  `Makefile`, `scripts/bootstrap.py`, `scripts/validate-manifest.py`,
  `scripts/validate-pins.py`, `contracts/{spec,code,shape}-pin.yaml` and
  `.github/workflows/validate.yml`; in each repository, `README.md`, `AGENTS.md`,
  `CLAUDE.md` and `.gitignore`.
- `.specify/` at the root, bootstrapped per the protocol.
- The root's own cutover runbook and proof document.
- `LICENSE` in each leg, the same Apache-2.0 bytes as the root's: openDox's three
  repositories are each Apache-2.0, and the scaffold sets no license (openxFactory's
  archived `split-opendox-two-layer-product` records that "the LICENSE TEXT stays
  a hand act").
- No carved path collides with a seed. Measured against openRepoShape
  `templates/` at `7f84ca4`, the assembly-root template seeds only
  `scripts/{bootstrap,validate-manifest,validate-pins}.py` and
  `contracts/{code,spec,shape,neutral-product}-pin.yaml` under the directories
  the carve also fills.

**The spec leg's OpenSpec gate — RULED "Vendor the tarball (Recommended)",
vendored fresh, NOT carved.** This repository's
`.github/workflows/openspec-cli-pin-gate.yml` opens "VENDORED from
opensoft/openxFactory@44d8fbaf…", and its one divergence — the vendored tarball —
rests on a ruling taken "for this repository's AGENTS.md rule 4". Carving it
would stretch that ruling to a repository it did not name. Instead the spec leg
gets the same shape under ITS OWN ruling:
- it commits the content-addressed tarball at
  `tools/openspec-cli-pin/fission-ai-openspec-1.12.0-c844543999f673cdd72445879b86a4abea4c07ef.tgz`,
  beside `contracts/openspec-cli-pin.yaml`, `scripts/install-pinned-openspec-cli.py`,
  `scripts/validate-openspec-cli-pin.py` and its drift-check document;
- its `.github/workflows/openspec-cli-pin-gate.yml` is vendored from openxFactory
  with ONE declared divergence, the final `run:` line passing `--no-cache
  --tarball` at that path, so the gate installs from the committed bytes
  OFFLINE;
- the leg's `AGENTS.md` records the ruling as its own offline-gate rule, as this
  repository's rule 4 carries the 2026-09-07 one.

The scripts resolve everything from their own root (`ROOT = parents[1]`,
`contracts/openspec-cli-pin.yaml`), so they run unchanged at the spec leg's root,
where `openspec/` lives. The `integrity` content address stays the trusted
referent. The gate is CI tooling that checks the leg's OpenSpec deltas, outside
every byte a consumer pins or runs, so the neutral standard's
no-openxFactory-input boundary — the code leg's run-time path and the root's
release identity — is unaffected.

**Stays here (`not_moved`).**
- The three `grant-review-*` negatives.
- `contract_pin.yaml`, `contracts/schemas/hermes-job-envelope.schema.yaml`,
  `scripts/verify-contract-pin.py`, `docs/pin-resync-runbook.md` and
  `docs/openxwallet-cutover-runbook.md`.
- The OpenSpec CLI pin tooling.
- `tests/per_seat_register_entries/`, `tests/register_reissuance/`,
  `tests/widen_register_reader/`, and the register half of
  `tests/nested_repo_prune/`.
- `openspec/specs/review-authority-register-reader/`,
  `openspec/changes/widen-register-reader-for-a-second-council/` and
  `openspec/changes/archive/2026-09-06-add-per-seat-register-entries/`.
- Speckit `specs/012-…`, `013-…` and `014-…`.
- `ideation/`, `.specify/` and `.github/workflows/lane-line.yml`.

### The validator under the shape

- **ROOT resolves to the code leg, and the diff does not grow.** The contracts
  sit in the same leg as the validator, with today's layout, so
  `ROOT = parents[1]` and every path under it (`:249-253`) resolve unchanged.
  Hunks (a)–(e) remain the whole diff. Under Q7's spec-leg alternative this
  fails: `CORE_DIR = ROOT / "contracts" / "openxwallet"` would name a path in
  another repository — a sixth hunk.
- **The nested-repository prune at the assembly root — MEASURED** (D0). Run from
  the assembly root, the validator prunes `code` and `spec` whole and scans
  nothing: exit 0 with `repo scan: 0 openxWallet artifact(s) validated, 0
  document(s) skipped as another kind`. `sweep_candidates` (`:3328-3398`) prunes
  every directory holding a `.git` entry, and a leg is one. A root-level run is
  therefore NOT a gate, and it is never wired as one.
- **Resolution: the wallet checks belong to the code leg.** `wallet-validation`
  and `pytest-suite` run in the code leg's own CI, from the leg's own root, with
  today's invocation (`python3 scripts/validate-openxwallet.py .`, measured from
  inside the leg: `20 document(s) skipped as another kind`, exit 0). The root's
  check is the shape's `validate`.
- **Consumers are unaffected.** A consumer scans its OWN root, where `openWallet/`
  — or `openXwallet/` above it — is pruned whole, as today.
- **The prune is not taught to descend into legs.** That would be a core edit no
  consumer needs, and it would change every consumer's output.

### Required checks, per repository

| Repository | Required check | Source |
|---|---|---|
| `opensoft/openWallet` (root) | `validate` — names, manifest, lockstep pins | the scaffold's copied workflow |
| `opensoft/openWallet-spec` | the leg's OpenSpec CLI pin gate | vendored for the leg (above) |
| `opensoft/openWallet-code` | `wallet-validation`, `pytest-suite` | carved workflows |

openDox requires a `validate` check in all three of its repositories; each of its
legs carries one that runs `pytest` (openDox `docs/branch-protection.md`,
`code/.github/workflows/validate.yml`). Whether each openWallet leg ALSO carries
a check named `validate` beside the checks above is the plan's call. Every
ruleset goes EVALUATE, then one trivial pull request so its checks report, then
ACTIVE; day-one REQUIRED is impossible.
- `scaffold-project.py` creates no ruleset.
- In `opensoft` the rulesets are organisation-sourced, so each one is an
  org-admin act. Both facts are recorded in openxFactory's archived
  `split-opendox-two-layer-product` proposal.

### Release identity at the root (Q4's placement, following openDox)

- **The release identity sits at the ROOT.** openDox's `contracts/manifest.yaml`
  (`contract_bundle_version: none`, `entries: []`) and `contracts/CHANGELOG.md`
  sit at its assembly root. openxFactory's archived `split-opendox-two-layer-product`
  puts the manifest, the CHANGELOG and the bundle tag there because the root "is
  the only object whose ONE commit names both legs: a tag on a leg describes half
  a project".
- **So, for openWallet:**
  - the annotated `wallet-v*` tag is cut on a ROOT commit;
  - `contracts/manifest.yaml`, `contracts/CHANGELOG.md` and `contracts/releases/`
    sit at the root;
  - the manifest's owned rows name `code/contracts/…`, the same strings
    openXwallet's pin `files:` hold;
  - each artifact's per-file `contract_schema_version` stays inside its bytes, in
    the code leg;
  - no leg is tagged.
- **The five values of AGENTS.md rule 6 are realized across one root commit and
  the leg commits it pins.** openDox has cut no release yet, so openWallet's first
  release is the first cut on this placement. The `contracts/releases/` records
  for v1.0…v1.5 are carried verbatim: they describe openXwallet commits and paths,
  and are history.

### The carve manifest

`docs/openwallet-carve-manifest.yaml`, in THIS repository, in openDox's grammar
(openxFactory `docs/opendox-carve-manifest.yaml`, 456 rows).

- **One row per tracked path at the carve commit:** `source_path`, `git_mode`,
  `sha256`, `destination` (`openwallet_root`, `openwallet_spec`,
  `openwallet_code`, or none), `destination_path`, and `disposition`
  (`moved_verbatim`, `moved_with_declared_edit` or `not_moved`).
- **The leg-classification overrides are DECLARED, not implied.**
  openRepoShape's classifier (`contracts/path-classification.yaml`, read by
  `scripts/path_classify.py`: "THE POLICY PROPOSES; A HUMAN DISPOSES") was run
  over this repository's tracked paths at `b7c6e0b`. Every path this design
  places agrees with its default except two groups, and each row in them carries
  the rule it overrides, the leg it takes, and its authority:
  - 73 rows — `contracts/openxwallet/**` and `contracts/openxwallet-agent-profile/**`,
    less the three `grant-review-*` negatives — default `spec` under
    `spec-governance` and go to the CODE leg. This override is RULED (Q7, "Code
    leg, declared override (Recommended)", recorded at 2026-10-08T17:01:43Z).
  - 9 rows — `contracts/manifest.yaml`, `contracts/CHANGELOG.md`, the six
    `contracts/releases/` records and `docs/byte-identity-wallet-v1.0.md` —
    default `spec` under `spec-governance` and go to the ROOT. This override is
    PROPOSED, following openDox's root release placement (Q4's placement, above),
    and is NOT covered by Q7's ruling.
- **One field openDox did not need, `retained_here`** (`kept`, `shed` or
  `retired_by_archive`). This carve leaves some carved records in place, so the
  adapter rebuild's shed is exactly the rows marked `shed`, and the two promoted
  specs leave only by this change's archive.
- **`destination_path` equals `source_path` on every moved row.** A tracked path
  in no row, or in two rows, REFUSES.
- **The edit classes are closed:**
  - validator hunks (a)–(e);
  - the test split;
  - the manifest field edits — `carved_from:`, each owned row's `path:` gaining
    `code/`, `source_path:`, and the consumed hermes row removed;
  - the eleven subject lines, plus the travelling change's three occurrences;
  - the code-leg workflow's envelope-verify step.

  **AMENDED 2026-10-08.** Brett Heap, operator authority, in session, by
  multiple choice, label verbatim: "Amend the manifest: 8 declared lines
  (Recommended)" (opensoft/openXwallet#25, comment 6068473776). The test split
  gains eight lines, and no class is added:
  - `tests/multi_key_wallets/test_declared_key_sets.py` :108-111 and :117-118.
    The `_grant` fixture's hermes-named posture keys are refused by Q6's
    fail-closed behaviour when no binding is declared, so that row becomes
    `moved_with_declared_edit`;
  - `tests/nested_repo_prune/test_prune_and_register_note.py` :47-48. The
    pinned corpus note becomes 21 / 42 / 11 of 11.

  The carve commit does not move.
- **The declared additions are closed too:** the corpus binding and the legs'
  `LICENSE`.

### Creation route

1. **[OPERATOR] Name check** for `openWallet`, `openWallet-spec` and
   `openWallet-code`: case variants in the organisation and an unscoped fork
   search, before anything is created. On any hit, stop. Today none of the three
   resolves.
2. **[OPERATOR] Scaffold** from a pinned openRepoShape commit, `--visibility
   public` passed explicitly (the tool's default is `private`):
   `scaffold-project.py --org opensoft --project openWallet --visibility public
   --elected-by "Brett Heap" --elected-on 2026-10-08`, or the guided `setup.sh`
   with the same flags.
   - The guided front door refuses `--org opensoft` without
     `--allow-upstream-org` (openRepoShape `setup-project.py:1270-1284`), because
     opensoft is openRepoShape's own upstream organisation.
   - openRepoShape's handbook says never to pass that flag on one's own
     initiative. Scaffolding into `opensoft` is Brett's act, and an agent never
     supplies the flag.
3. **Carve per destination.** From a FRESH clone at the carve commit, run
   `git filter-repo` with one exact `--path` per moved row for that destination:
   no globs, no `--path-rename`, full history. Merge the result into the seeded
   repository with `--allow-unrelated-histories`. Legs first, then the root, in
   ONE root commit that merges the root's carve layer and moves each leg's
   gitlink and its `contracts/{code,spec}-pin.yaml` together — the lockstep
   invariant.
4. **The declared-edit layer** per destination, one auditable diff each, on the
   pure carve.

**Rejected: openRepoShape's `adopt-project.py`**, which adopts an existing
repository in place as the assembly root. There is no root to adopt, and the
ruling is "at birth".

### The contracts' leg — RULED Q7

**RULED — "Code leg, declared override (Recommended)"**, as recommended.
Recorded at 2026-10-08T17:01:43Z; taken in session minutes earlier by multiple
choice.

Contracts, corpus and validator stay together in `opensoft/openWallet-code` at
today's repository-relative paths, and the override of openRepoShape's
`spec-governance` default is declared in the carve manifest (above). So every
path, pin string and literal in D5, D6 and this section stands as written.
openRepoShape's default and openDox's precedent put contracts in the SPEC leg.
The ruling declined that alternative, and its costs stay on record in the
proposal's Q7:
- hunk count (a sixth);
- the pin's `files:` (split across `spec/` and `code/`);
- the consumer inits (both legs);
- openxFactory's re-path (split).

### The proof — a DECLARED PATH MAPPING

`docs/byte-identity-<first openWallet tag>.md`, at the openWallet ROOT. Each part
can fail:

| Part | Claim |
|---|---|
| zero | control: the eight recorded sha256s recomputed at the carve commit, 8/8, or a later match proves the manifest stale rather than the carve faithful |
| one (a) | the MAPPING is total and functional: every tracked path at the carve commit sits in exactly one manifest row; every moved row's `destination_path` equals its `source_path`; per destination, the sorted `ls-tree` of the carve layer equals that destination's rows, with explicit counts (68 + 8 contract files less 3; 41 + 4 negatives less 3, at `b7c6e0b`), the `examples/` prefixes preserved because `repo_scan`'s exclusion keys on them |
| one (b) | the eight digests THREE-WAY: the carve-commit manifest's `sha256:` = the bytes at `contracts/…` in the code leg's carve layer = the openWallet root manifest's rows at `code/contracts/…` |
| two (a) | per destination, git blob + mode identity 100% at the carve layer, recorded per path |
| two (b) | the declared-edit layer: every changed validator line falls in hunk (a)–(e), every other changed path in its declared class, every added path among the declared additions; a line or path in no class REFUSES |
| three | behaviour, run from the CODE leg's own root: openWallet standalone reports 21 / 42 / 11 of 11 and refuses a posture under no binding; D5's neutrality gate is empty over the composed adapter |
| four | every verifier observed REFUSING a mutated input before it is trusted, including a root whose `code` gitlink and `contracts/code-pin.yaml` disagree |
| five | the shape's `validate` green at the root: names, manifest, lockstep pins |

A consumer sees one prefix and nothing else:
- a path `P` in the code leg is `openWallet/code/P` inside openXwallet;
- it is `openXwallet/openWallet/code/P` inside openxFactory;
- its sha256 is the same at every depth.

**Then rulesets, then the tag.** Three rulesets, per the table above. The first
`wallet-v*` tag goes on the root only after the proof is green.

## D8 — Spec movement

**Here:** `## REMOVED Requirements` for all eleven, titles character-for-
character, successor recorded in each, in the precedent's form. The capability
`openxwallet-factory-binding` is ADDED; `review-authority-register-reader` takes
no delta.

**There:** the specs arrive by the carve in openWallet's SPEC leg, and
openWallet's own birth change, authored in that leg's OpenSpec instance,
MODIFIES exactly one requirement. Its successor text, drafted here so the
substance is ratified with this packet:

> **Agent authority is grant scope, not a parallel vocabulary.** openWallet SHALL
> express what an agent may do as the SCOPE of a capability grant, and SHALL
> admit as legal approval-posture terms exactly the keys of ONE DECLARED
> VOCABULARY BINDING supplied by the consuming layer and read at run time, never
> restated, so that an agent's authority and a job's approval posture are stated
> in one vocabulary rather than two kept in agreement. Absent a declared binding,
> a grant naming any approval posture SHALL be refused. Scenarios: authority is
> carried by a grant (unchanged); the bound vocabulary is reused, not duplicated;
> no binding is declared, so a posture is refused rather than admitted because
> nothing forbade it.

**OXWR-R1 / OXWR-R2 get a home-side heading for the first time.** They have had
validator rows and no `### Requirement:` here since the carve (logged by
`add-composition-drift-cascade`'s design). `openxwallet-factory-binding`'s
requirement (iii) states what they enforce and where it came from.

## D9 — What travels with which change

`add-multi-key-wallets` archives HERE first, and its archive record is carved.
`add-composition-drift-cascade` is carved into openWallet's spec leg as an
active change and deleted here in the adapter rebuild; there its three
`openXwallet` occurrences take
the subject rewrite, and its MODIFIED *Revocation propagates through the chain*
is REBASED onto the text multi-key's archive promotes before it archives. On the
pinned CLI that archive ABORTS until the rebase is done (D0); Q-WRR-4 had assumed
a silent overwrite. `widen-register-reader-for-a-second-council` stays and is
independent.
This change archives here last, after the reflow D0 measured as its
precondition.

## Migration plan

Ordered; each rollback is written before its step.

1. **Ratify.** Q1–Q7 and the spec leg's gate are ruled (2026-10-08).
   *Rollback:* none needed — nothing has moved.
2. **Archive `add-multi-key-wallets` here, then reflow the promoted specs'
   wrapped scenario lines (D0).** *Rollback:* revert either commit.
3. **openWallet's birth: three public repositories.**
   - [OPERATOR] the name checks for all three;
   - [OPERATOR] the scaffold into `opensoft`, public, with the ruling's
     `elected_on`;
   - the root's cutover runbook;
   - `.specify/` at the root;
   - the spec leg's own OpenSpec gate, installing its committed tarball
     offline;
   - the birth change in the spec leg's OpenSpec instance.

   *Rollback:* delete the three repositories; nothing pins them.
4. **Carve the legs, then the root (one lockstep commit); the declared edits;
   the path-mapping proof (D7).** The carve runs at the named carve commit
   `90111df262d6f54f7e82651d860adc12345f83f4` (D7, task 2.3). *Rollback:*
   delete the three repositories; the carve copied, and this repository is
   untouched.
5. **[OPERATOR] Three rulesets, then the first tag, on the root.** *Rollback:*
   delete the tag; nothing pins it yet.
6. **The adapter rebuild here, one pull request.**
   - the `openWallet` gitlink at the root;
   - the pin with its code-leg lockstep, and its verifier;
   - the two-line nested init;
   - the composed validator over `openWallet/code/`;
   - the shed per the carve manifest's `retained_here: shed` rows;
   - the docs.

   D5's neutrality gate must be green. *Rollback:* revert the pull request; every
   shed path returns.
7. **The adapter's first tag.** *Rollback:* delete it before any consumer pins
   it.
8. **openxFactory, one pull request in its repository.**
   - re-path under `openWallet/code/` and bump;
   - the three-line scoped init, with its remediation trailer and its test;
   - two-level nested parity;
   - the trust-anchor literal.

   Its literal assertions must be green and UNCHANGED. *Rollback:* revert; its pin
   returns to `wallet-v1.5`, where every path still exists.
9. **Consumer notices and verifications** — LedgerxWallet, LedgerxFactory,
   codexFactory's floor, the aggregation.
10. **Archive this change** on merged, green realization evidence.

## Risks

- **Four-level depth.** LedgerxFactory reaches the core at
  `openxFactory/openXwallet/openWallet/code/`; its finder is as the precedent
  measured it, and LedgerxFactory is not re-measured here. A scoped init that
  stops a level short is exit 2 with a named refusal that names the missing
  level, which is loud by design. Each consumer task names its init lines.
- **A root-level wallet run looks green and checks nothing** (MEASURED, D0).
  Mitigation: it is never wired as a check. The code leg's checks are the gate,
  and the proof's part three runs from the code leg's root.
- **Q7's override of openRepoShape's default.** openRepoShape's path
  classification sends `contracts/**` to the spec leg. A later `update-shape`,
  an adoption check or a reviewer reading the default may flag the code leg's
  contracts. Mitigation: the override is RULED (Q7) and declared in the carve
  manifest on every row it governs, naming the rule it overrides; the root's
  `AGENTS.md` points to that declaration.
- **The upstream-organisation scaffold.** Scaffolding three repositories into
  `opensoft` is refused by the guided front door without
  `--allow-upstream-org`. It is Brett's act, and a run that supplies the flag on
  an agent's initiative is a defect.
- **The release identity spans three repositories.** A consumer that pinned a leg
  directly would bypass the root's release identity. Mitigation: openXwallet pins
  the ROOT and verifies the code leg by lockstep, so the root commit stays the
  single answer to "which openWallet".
- **Visibility.** Ruled public (Q5). A leg created private by the tool's default
  would bring the App token back into every CI that initializes it, so the
  scaffold passes `--visibility public` explicitly, and the name check records all
  three repositories' visibility afterwards.
- **Coverage closure in two repositories.** It holds by the attribution D0
  measured. The proof's part three asserts 11/11, 2/2 and 13/13 rather than
  trusting that measurement to stay true.
- **Stale prose inside digested bytes.** The grant schema's description and the
  `approval_posture` comment (`contracts/openxwallet/openxwallet-grant.schema.yaml:25-32`,
  `:80-85`) say the validator reads the envelope; in openWallet that becomes
  untrue. Correcting it moves a digest, so it waits for the next digest-moving
  release and is declared, not hidden. The `issued_by` comment (`:90-97`) names
  the Human Escalation Contract, for the same reason and with the same wait.
- **Internal coupling.** The adapter reaches core internals (`Context`,
  `Findings`, `validate_record`). The extension points are the contract, and
  openWallet's own tests pin them. The adapter moves only on a pin bump, so a core
  refactor breaks the adapter's pull request rather than a consumer.
- **The publisher-marker test.** The adapter still carries
  `contracts/manifest.yaml`, `contracts/schemas/` and a file named like the
  family validator — openxFactory `shared-contract-ownership`'s markers. The
  adapter's manifest must claim nothing it does not own; this is re-read at
  realization.
- **Archive ordering.** Every abort in D0's table is loud, not silent, on the
  pinned CLI. The risk is a wave stalled at its last step; D9's order and the
  pre-carve reflow prevent it.

## Rejected alternatives, collected

- **Mirror copies.** They give a second answer to which bytes are current.
- **Renaming in the same act.** It is ruled out, and it is unbisectable inside a
  move.
- **Subprocess or sequential composition** (D5).
- **Rule (t) kept in the core behind an anchor parameter.** The anchor means
  something only against a register and an escalation contract, both factory
  concepts.
- **The reader split back into openxFactory** (the precedent's Q1 second limb).
  It unpins "which reader ran".
- **A direct openWallet mount in openxFactory** (D6).
- **ONE repository for openWallet.** It was Q3's recommendation, and Brett's
  ruling overrode it.
- **openRepoShape's adopt route** (D7).
- **A root-level wallet gate** (D7, measured to scan nothing).
- **Teaching the prune to descend into legs** (D7).
- **A recursive consumer init** (D6).
- **Tags on legs** (D7).
- **Carving the vendored OpenSpec gate into the spec leg** (D7).
- **Vendoring the envelope into openWallet** (D4).
- **Contracts in the spec leg.** This was Q7's alternative; the ruling declined
  it, and its costs stay on record in the proposal.

## What this design does not decide

- **The plan's calls:**
  - the exact spelling of the binding's CLI form;
  - the corpus binding's filename;
  - the extension points' names;
  - whether each openWallet leg also carries a check named `validate`.
- **Fixed at the scaffold:** the openRepoShape commit the scaffold runs from,
  pinned there by commit and digest.
- **Realization's:** every release number.
- **Constrained in D6, not chosen:** whether the adapter's manifest keeps consumed
  rows for the eight.
- **The plan's, under the ruled gate shape:** the openxFactory commit the spec
  leg's gate workflow is vendored from.
- **Not in scope:** any domain wallet's content.

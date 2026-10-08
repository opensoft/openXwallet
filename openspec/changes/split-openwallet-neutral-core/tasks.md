# Tasks: split-openwallet-neutral-core

Lane: openXwallet-2

OpenSpec ratifies the boundary; Speckit builds it. Each group from §2 on is
realized as its own Speckit feature in `design.md`'s migration order, and
nothing from §2 on is legal before §1.2 is ticked.

**Tags.** Untagged = openXwallet. The openWallet PROJECT is three repositories
(RULED Q3): `[openWallet-root]` = `opensoft/openWallet`, the assembly root;
`[openWallet-spec]` = `opensoft/openWallet-spec`; `[openWallet-code]` =
`opensoft/openWallet-code`; `[openWallet]` = all three. `[openxFactory]`,
`[LedgerxWallet]`, `[LedgerxFactory]`, `[codexFactory]`, `[xFactory]` = that
repository. `[OPERATOR]` = only Brett can perform it — a ratification, a
repository creation, a scaffold into `opensoft`, a ruleset, a tag.
`[GOVERNANCE]` = it needs a ruling first.

## 1. Governance

- [x] 1.1 Author this packet. `python3 scripts/validate-openspec-cli-pin.py --all
      --no-cache --tarball tools/openspec-cli-pin/fission-ai-openspec-1.12.0-c844543999f673cdd72445879b86a4abea4c07ef.tgz`
      clean at `--strict` for every change and spec.
- [x] 1.2 **[OPERATOR] [GOVERNANCE]** Ratify or return this proposal. The prefix
      ("keep the prefix"), Q1–Q7 and the spec leg's gate (3.6) are already
      RULED and are not re-asked.
      **RATIFIED** — Brett Heap, operator authority, 2026-10-08T17:10:47Z,
      verbatim: "ratify 26 and merge" (head
      `2ae4eee1885536297e5653e64b6abb1b85cc8e9e`).
      See `proposal.md` "## Status". Ruling:
      https://github.com/opensoft/openXwallet/pull/26#issuecomment-6065121015
- [x] 1.3 Q1–Q6 RULED by Brett Heap in session on 2026-10-08, by multiple
      choice — recorded at 2026-10-08T16:30:50Z; taken in session minutes
      earlier by multiple choice — and encoded beside their questions in
      `proposal.md`, in `design.md` D4–D7, and in `.openspec.yaml`
      `origin.rulings`. Q3 overrode its recommendation; the packet was reworked
      to the three-leg shape, and the pinned CLI gate re-run clean.
- [x] 1.3a Q7 and the spec leg's OpenSpec-gate question (3.6), both raised by
      Q3's ruling, RULED by Brett Heap in session on 2026-10-08, by multiple
      choice — recorded at 2026-10-08T17:01:43Z; taken in session minutes
      earlier by multiple choice:
      - Q7 "Code leg, declared override (Recommended)": contracts, corpus and
        validator stay together in `opensoft/openWallet-code` at today's
        relative paths, and the override of openRepoShape's `spec-governance`
        default is declared in the carve manifest (2.5);
      - 3.6 "Vendor the tarball (Recommended)".

      Both are encoded in `proposal.md`, `design.md` D7 and `.openspec.yaml`
      `origin.rulings`.
- [ ] 1.4 On ratification: `Status: ratified`, the `Ratified:` line with the word
      verbatim, and `.openspec.yaml` `approved_by` / `approved_on` filled. Every
      question is already ruled and encoded beside itself.

## 2. Before the carve — this repository

- [ ] 2.1 Archive `add-multi-key-wallets` with the pinned CLI (its realization
      evidence is in its own `tasks.md`), so its four MODIFIED requirements are
      promoted text before they travel.
- [ ] 2.2 Reflow the wrapped scenario-bullet lines in the promoted
      `openxwallet` and `openxwallet-agent-profile` specs onto their bullets — an
      editorial, content-preserving commit ratified by this change, as
      `add-multi-key-wallets` task 6.4 ratified its own `## Purpose` edit.
      MEASURED on 1.12.0 (`design.md` D0): seven such lines after 2.1, and this
      change's archive cannot retire the capabilities while they stand.
- [ ] 2.3 Name the CARVE COMMIT: an openXwallet `main` commit after 2.2, never
      HEAD.
- [ ] 2.4 Re-measure every line range in `design.md` D3 at that commit; a range
      that moved is corrected in the plan, never assumed.
- [ ] 2.5 Author `docs/openwallet-carve-manifest.yaml` at the carve commit, in
      openDox's grammar plus `retained_here` (`design.md` D7): one row per
      tracked path, `destination_path` equal to `source_path` on every moved
      row; a tracked path in no row or in two rows REFUSES. Every row whose leg
      departs from openRepoShape's `path-classification.yaml` default carries
      the rule it overrides and its authority: the 73 contract rows to the code
      leg under RULED Q7, and the 9 release-identity rows to the root as
      PROPOSED (`design.md` D7).

## 3. openWallet's birth — three public repositories `[openWallet]`

- [ ] 3.1 **[OPERATOR]** The name check for `openWallet`, `openWallet-spec` and
      `openWallet-code` — case variants in the organisation and an unscoped fork
      search — recorded BEFORE creation. On any hit, stop.
- [ ] 3.2 **[OPERATOR]** The scaffold, from a pinned openRepoShape commit:
      `scaffold-project.py --org opensoft --project openWallet --visibility
      public --elected-by "Brett Heap" --elected-on 2026-10-08`, or the guided
      `setup.sh` with the same flags. The guided front door refuses `--org
      opensoft` without `--allow-upstream-org`, which is Brett's to pass and
      never an agent's.
- [ ] 3.3 Verify the scaffold's `project.yaml` against `design.md` D7:
      - `elected_by: "Brett Heap"`, `elected_on: 2026-10-08`;
      - `topic: xf-project-openwallet`, `visibility: public`, `tracking_branch: main`;
      - `shape:` pinning openRepoShape by commit and `sorted-ls-tree-r-v1` tree
        digest, equal to `contracts/shape-pin.yaml`;
      - `neutral_product_pins: []`;
      - the three legs with their `naming:` records.

      Then check GitHub: `gh repo view` reads PUBLIC for all three, and each
      repository carries the topic.
- [ ] 3.4 `[openWallet-root]` The cutover runbook, authored BEFORE the carve, a
      rollback per phase written before the phase; `.specify/` bootstrapped at
      the root.
- [ ] 3.5 `[openWallet]` Each repository's `README.md`, `AGENTS.md`, `CLAUDE.md`
      and `.github/CODEOWNERS`. The root's `AGENTS.md` points, beside
      `AGENTS-shape.md`, to the carve manifest's declared Q7 override.
- [ ] 3.6 `[openWallet-spec]` The leg's own OpenSpec gate — RULED 2026-10-08,
      "Vendor the tarball (Recommended)" (recorded at 2026-10-08T17:01:43Z).
      - The leg commits the content-addressed `@fission-ai/openspec@1.12.0`
        tarball at
        `tools/openspec-cli-pin/fission-ai-openspec-1.12.0-c844543999f673cdd72445879b86a4abea4c07ef.tgz`,
        beside `contracts/openspec-cli-pin.yaml`,
        `scripts/install-pinned-openspec-cli.py`,
        `scripts/validate-openspec-cli-pin.py` and the drift-check document.
      - Its `.github/workflows/openspec-cli-pin-gate.yml` mirrors this
        repository's: vendored from openxFactory at a named commit, byte-identical
        except ONE declared divergence, the final `run:` line passing `--no-cache
        --tarball` at the committed path, so the gate installs OFFLINE.
      - The leg's `AGENTS.md` records the ruling as its own offline-gate rule —
        the same per-repository pattern as this repository's rule 4 and its
        2026-09-07 ruling.
      - Vendored fresh, NOT carved (`design.md` D7).
      - The gate is OBSERVED refusing a mutated tarball before it is trusted,
        and is green over the leg's `openspec/` at `--strict`.

## 4. The carve, the path-mapping proof, the first release `[openWallet]`

- [ ] 4.1 The CONTROL: the eight recorded sha256s recomputed at the carve
      commit, 8/8, before anything is carved.
- [ ] 4.2 `[openWallet-code]` Carve the carve manifest's `openwallet_code` rows:
      `git filter-repo` from a fresh clone, one exact `--path` per row, no globs,
      no `--path-rename`, full history. Merge into the seeded leg with
      `--allow-unrelated-histories`. Blob and mode identity 100% at the carve
      layer; both `examples/` prefixes preserved.
- [ ] 4.3 `[openWallet-spec]` The same for the `openwallet_spec` rows.
- [ ] 4.4 The declared-edit layer per leg, one auditable diff each.
      - Code leg: validator hunks (a)–(e); the corpus binding added (Q6); the
        `tests/nested_repo_prune/` split; `wallet-validation`'s envelope-verify
        step removed; `LICENSE` added.
      - Spec leg: the eleven subject lines; the three `openXwallet` occurrences in
        `add-composition-drift-cascade`'s deltas; `LICENSE` added.
- [ ] 4.5 `[openWallet-root]` Carve the `openwallet_root` rows and apply the
      manifest's declared field edits:
      - `carved_from:`;
      - each owned row's `path:` gaining `code/`;
      - `source_path:`;
      - the consumed hermes row removed.

      Do it in ONE root commit that also moves both gitlinks and
      `contracts/{code,spec}-pin.yaml` in lockstep. The shape's `validate` is
      green.
- [ ] 4.6 `[openWallet-root]` The proof, `docs/byte-identity-<first tag>.md`,
      parts zero to five of `design.md` D7 — the DECLARED PATH MAPPING — each
      able to fail. A validator line in no declared hunk, or a path in no
      declared class, REFUSES it. Part three runs from the code leg's own root.
- [ ] 4.7 **[OPERATOR]** Three rulesets, each EVALUATE → one trivial pull request
      so its checks report → ACTIVE. Each is an org-admin act in `opensoft`.
      - root: `validate`;
      - spec leg: its OpenSpec gate;
      - code leg: `wallet-validation` and `pytest-suite`.
- [ ] 4.8 `[openWallet-spec]` openWallet's birth change in the leg's own
      OpenSpec instance, after 4.3 lands. It MODIFIES *Agent authority is grant
      scope, not a parallel vocabulary* to the text drafted in `design.md` D8.
- [ ] 4.9 **[OPERATOR]** `[openWallet-root]` First release — five coordinated
      values — on the ROOT:
      - the annotated `wallet-v*` tag on the root commit that pins both legs;
      - `contracts/manifest.yaml`, `contracts/CHANGELOG.md` and
        `contracts/releases/` at the root;
      - no leg tag;
      - the tag only after 4.6 is green;
      - the number allocated here, not before.

## 5. The adapter rebuild — this repository, one pull request

- [ ] 5.1 The gitlink `openWallet/`, mounting the openWallet ROOT, and
      `contracts/openwallet-pin.yaml` in the same commit. The pin holds:
      - the root `commit:`;
      - `legs.code`, as a lockstep mirror;
      - `files:` at `code/contracts/…`;
      - `pinned_by_commit_only:` at `code/…`.

      `scripts/verify-openwallet-pin.py` fails closed. It is OBSERVED refusing an
      uninitialized `openWallet/`, an uninitialized `openWallet/code/`, a
      gitlink ≠ pin, a checkout ≠ pin, a leg-lockstep mismatch (the root's `code`
      gitlink vs its `contracts/code-pin.yaml` vs `legs.code.commit`, read from
      git objects) and a mutated digest.
- [ ] 5.2 `scripts/validate-openxwallet.py` recomposed per `design.md` D5:
      - the pinned core loaded in process from
        `openWallet/code/scripts/validate-openxwallet.py`;
      - rule (t) and the register reader registered at their present positions;
      - the hermes binding unconditional.
- [ ] 5.3 `scripts/wallet-yaml-syntax-gate.py` kept as an entrypoint, one
      implementation.
- [ ] 5.4 THE NEUTRALITY GATE: the carve-commit validator and the composed
      adapter over this tree, an export of openxFactory's live `governance/`
      tree, and every test-suite fixture tree — `diff` EMPTY, plain and
      `--strict`, the same exit code. This tree's one new prune note is declared.
- [ ] 5.5 Shed exactly the carve manifest's `retained_here: shed` rows —
      `add-composition-drift-cascade` among them. Leave the `kept` rows (the three
      adapter negatives at their path, every archive record unedited) and the
      `retired_by_archive` rows (the two promoted specs, which this change's
      archive retires).
- [ ] 5.6 Manifest (nothing of openWallet's registered as owned), CHANGELOG,
      README (the adapter role, PUBLIC, the Speckit list, the capability count),
      AGENTS.md (the one-paragraph identity and rule 3), CODEOWNERS.
      `wallet-validation` runs in this order: `git submodule update --init
      openWallet`, then `git -C openWallet submodule update --init code`, then
      the two verifiers, then the gates.
- [ ] 5.7 The full gate bar (AGENTS.md rule 5) and the pinned CLI gate, green.
- [ ] 5.8 **[OPERATOR]** The adapter's first release in Q4's series, five
      values, tagged at the merge commit.

## 6. openxFactory — one pull request `[openxFactory]`

- [ ] 6.1 `contracts/openxwallet-pin.yaml`:
      - `files:` re-pathed to `openWallet/code/contracts/…`;
      - `pinned_by_commit_only:` keeps `scripts/validate-openxwallet.py` and
        `scripts/wallet-yaml-syntax-gate.py`, re-paths the corpora and READMEs to
        `openWallet/code/contracts/…`, and adds
        `openWallet/code/scripts/validate-openxwallet.py` and
        `openWallet/code/scripts/wallet-yaml-syntax-gate.py`;
      - `commit:` and `contract_bundle_tag:` bumped;
      - the eight digests re-verified by recomputation (values unchanged);
      - no openWallet commit recorded (ONE chain).
- [ ] 6.2 `.github/workflows/openxwallet-consumer-gate.yml` (`:99`): the scoped
      init extended to three named levels — `openXwallet`, then
      `openXwallet/openWallet`, then its `code` leg — never `--recursive`. In the
      same commit: `tests/openxwallet_consumer_gate/test_gate_invocation.py`
      (its `SCOPED_INIT_RUN`, `:47`), and `scripts/verify-openxwallet-pin.py`'s
      remediation trailer (`:80-89`, FR-004).
- [ ] 6.3 `scripts/verify-openxwallet-pin.py`: nested-checkout parity through BOTH
      levels, observed refusing at each.
- [ ] 6.4 `scripts/validate-trust-anchor.py` `OPENXWALLET_REGISTRY_PATH`
      (`:348-350`) becomes `ROOT / "openXwallet" / "openWallet" / "code" /
      "contracts" / "openxwallet" / "openxwallet-custody.registry.yaml"`, with
      `tests/trust-anchor/test_openxwallet_pin_refusal.py` (`:199`) in the same
      commit.
- [ ] 6.5 The gate's LITERAL assertions do not move and are green — `8 of 8`,
      the five-key wallet note, `repo scan:`.
- [ ] 6.6 `doc-health-reusable.yml`'s nested init — only if a leg reads wallet
      content; checked, not assumed.

## 7. Consumer notices and verifications

- [ ] 7.1 `[LedgerxWallet]` Nothing on day one. At its next pin bump, the
      nested init of `openXwallet/openWallet` and its `code` leg. One direct
      upstream per Q2.
- [ ] 7.2 `[LedgerxFactory]` Its estate run initializes two levels deeper, to
      `openxFactory/openXwallet/openWallet/code`. Its `--strict` run and its
      `repo scan:` parse stay green.
- [ ] 7.3 `[codexFactory]` Confirm `openxfactory_floor.py` still floors the
      `openXwallet` gitlink and that Q2 adds no second wallet gitlink; record it.
- [ ] 7.4 `[xFactory]` No root `openWallet` gitlink under Q2; if one is ever
      added, root-gitlink parity against openXwallet's pin.

## 8. Travels with openWallet — named, not this change's gate

- [ ] 8.1 `[openWallet-spec]` Rebase `add-composition-drift-cascade`'s MODIFIED
      *Revocation propagates through the chain* onto the text multi-key's
      archive promoted, before that change archives.
- [ ] 8.2 `[openWallet]` After the carve, never in it: the root manifest's stale
      corpus counts, and the code leg validator's `:337` pointer.
- [ ] 8.3 Named successors: the neutral-prefix MAJOR (deferred by ruling), rule
      (h)'s neutral re-expression, and the grant schema's envelope prose at the
      next digest-moving release.

## 9. Archive gate

- [ ] 9.1 `code_surface` is not `none`, so per `release-realization` this change
      archives only on MERGED, GREEN realization evidence: §2–§6 merged and
      green, the neutrality gate empty, §7 recorded.
- [ ] 9.2 `add-composition-drift-cascade` has LEFT this repository first — a
      MODIFIED delta against a retired spec aborts on 1.12.0 (measured,
      `design.md` D0) — and `retire_capabilities: true` is still declared.
- [ ] 9.3 The full gate bar re-run at archive.

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

- [x] 2.1 Archive `add-multi-key-wallets` with the pinned CLI (its realization
      evidence is in its own `tasks.md`), so its four MODIFIED requirements are
      promoted text before they travel.
      **DONE 2026-10-08** —
      `openspec/changes/archive/2026-10-08-add-multi-key-wallets/`, archived
      with the pinned @fission-ai/openspec@1.12.0 via
      scripts/install-pinned-openspec-cli.py (`~ 4 modified` to `openxwallet`,
      as D0 measured). Archive-time evidence and the full gate bar are recorded
      in that directory's `tasks.md`. Measured there: the pinned gate reads
      5 passed, 1 failed — `add-composition-drift-cascade`'s MODIFIED
      *Revocation propagates through the chain* omits the promoted scenario
      "retiring one key does not revoke the wallet", the collision D0 recorded;
      its cure is 8.1's rebase, not this task's.
- [x] 2.2 Reflow the wrapped scenario-bullet lines in the promoted
      `openxwallet` and `openxwallet-agent-profile` specs onto their bullets — an
      editorial, content-preserving commit ratified by this change, as
      `add-multi-key-wallets` task 6.4 ratified its own `## Purpose` edit.
      MEASURED on 1.12.0 (`design.md` D0): seven such lines after 2.1, and this
      change's archive cannot retire the capabilities while they stand.
      **DONE 2026-10-08**, landed by the reflow PR. Seven joins, all in
      `openxwallet` (line numbers as at `c1c97e5`; continuation joined onto
      its bullet with one space): 41+42 "record of another holder's key",
      56+57 "before sets were expressible", 130+131 "failure", 138+139
      "custody, never about adding a stronger key beside it", 168+169 "than
      passed over", 170+171 "keys signed", 222+223 "constraint named".
      `openxwallet-agent-profile` has none, by the same measurement. The
      whitespace-insensitive diff of the spec before and after is EMPTY. In a
      scratch copy on the pinned 1.12.0, `archive split-openwallet-neutral-core
      --yes` WITHOUT the reflow still refuses ("'openxwallet' declares
      retire_capabilities, but the spec holds content the merge cannot safely
      account for …", aborted), and WITH it reads `Totals: + 5, ~ 0, - 11`,
      both capability specs retired and `openxwallet-factory-binding`
      created, as D0 measured. Not archived in this tree.
- [x] 2.3 Name the CARVE COMMIT: an openXwallet `main` commit after 2.2, never
      HEAD.
      **DONE 2026-10-08** — `CARVE_COMMIT =
      90111df262d6f54f7e82651d860adc12345f83f4`, `main` at the merge of PR #28,
      after 2.1 and 2.2. Named by Brett Heap, operator authority, in session,
      2026-10-08T18:07:19Z, verbatim: "name 90111df as the carve commit, do 2.4
      and 2.5"; recorded on issue #25
      (https://github.com/opensoft/openXwallet/issues/25#issuecomment-6066081858).
      Written into `design.md` D7 and the Migration plan, and into
      `proposal.md`'s `code_surface`.
- [x] 2.4 Re-measure every line range in `design.md` D3 at that commit; a range
      that moved is corrected in the plan, never assumed.
      **DONE 2026-10-08** — at `90111df`, every range D3 cites was re-read with
      `grep -n` for its anchor and `sed -n` for its first and last line. Covered:
      the constants, `ENVELOPE_SCHEMA_PATH`, rule (t)'s constants and check, the
      (f)/(h) literals, the requirement rows, the self-test blocks, the register
      block, `sweep_candidates`, `repo_scan` with its `check_register` call, and
      `main()`'s envelope exit, vocabulary read and note. Also re-read:
      `contracts/manifest.yaml:69-70`. Every range is unchanged, and the
      validator is the same blob as at `b7c6e0b` (`08a4b5c7`). So no range was
      corrected. One imprecision, not a move, is recorded in D3: the `:337`
      pointer's path literal sits on `:338`.
- [x] 2.5 Author `docs/openwallet-carve-manifest.yaml` at the carve commit, in
      openDox's grammar plus `retained_here` (`design.md` D7): one row per
      tracked path, `destination_path` equal to `source_path` on every moved
      row; a tracked path in no row or in two rows REFUSES. Every row whose leg
      departs from openRepoShape's `path-classification.yaml` default carries
      the rule it overrides and its authority: the 73 contract rows to the code
      leg under RULED Q7, and the 9 release-identity rows to the root as
      PROPOSED (`design.md` D7).
      **DONE 2026-10-08** under the same ruling as 2.3 —
      `docs/openwallet-carve-manifest.yaml`, `carve_commit` `90111df`,
      `phase: carve`. Checked by `scripts/validate-carve-manifest.py` (it
      mirrors openxFactory's checker, adapted to this grammar), which
      `tests/carve_manifest/test_carve_manifest.py` drives in `pytest-suite`.
      - Rows: 232, one per tracked path.
      - Dispositions: 120 `moved_verbatim`, 8 `moved_with_declared_edit`,
        104 `not_moved`.
      - Legs: 80 `openwallet_code`, 38 `openwallet_spec`, 10
        `openwallet_root`.
      - `retained_here`: 124 `kept`, 106 `shed`, 2 `retired_by_archive`.
      - Overrides: openRepoShape's classifier at `7f84ca4` was run over all
        232 paths. Exactly 82 moved rows depart from its default, all from
        `spec-governance`: 73 under RULED Q7 and 9 PROPOSED. D7's 73 and 9
        held.
      - Declared edits: 1,884 lines on the 8 edited rows, in D7's five
        classes.
      - Checker verdict at `90111df`: `OK … 128 digest(s) recomputed …
        232 tracked path(s) at the carve commit, each in exactly one row`.
      - CI: the new `.github/workflows/carve-manifest.yml` (job
        `carve-manifest`, `fetch-depth: 0`) runs the checker and the test.
        `pytest-suite`, which is depth 1 and a carved row, is not edited; there
        the real-repository test skips loudly, naming `90111df` and that
        workflow. Making `carve-manifest` REQUIRED is Brett's console act.

## 3. openWallet's birth — three public repositories `[openWallet]`

- [x] 3.1 **[OPERATOR]** The name check for `openWallet`, `openWallet-spec` and
      `openWallet-code` — case variants in the organisation and an unscoped fork
      search — recorded BEFORE creation. On any hit, stop.
      **DONE 2026-10-08**, before creation, on Brett Heap's word in session,
      verbatim: "start group 3". `gh repo view` for `opensoft/openWallet`,
      `opensoft/openWallet-spec`, `opensoft/openWallet-code` and the case
      variants `openwallet`, `openwallet-spec`, `openwallet-code` and
      `OpenWallet`: none resolved. `gh search repos openwallet --owner
      opensoft`: no hit. The unscoped search found three unrelated third-party
      repositories named openwallet or OpenWallet under other owners
      (blocktree, Abhimanyu121, kyai), none a fork and none in the
      organisation. No hit, so no stop. Recorded on issue #25
      (https://github.com/opensoft/openXwallet/issues/25#issuecomment-6067172637).
- [x] 3.2 **[OPERATOR]** The scaffold, from a pinned openRepoShape commit:
      `scaffold-project.py --org opensoft --project openWallet --visibility
      public --elected-by "Brett Heap" --elected-on 2026-10-08`, or the guided
      `setup.sh` with the same flags. The guided front door refuses `--org
      opensoft` without `--allow-upstream-org`, which is Brett's to pass and
      never an agent's.
      **DONE 2026-10-08** on Brett Heap's word in session, verbatim: "start
      group 3". Run from openRepoShape `main` at
      `7f84ca42ca86a8902928345109d2bf6bad87bd91` (tree `3be52767e727…`),
      after a `--dry-run` that matched `design.md` D7 line for line, with
      exactly the flags above. Created and pushed, all PUBLIC, topic
      `xf-project-openwallet`, default branch `main`:
      - assembly `opensoft/openWallet` at `84a0569e3b81`;
      - spec leg `opensoft/openWallet-spec` at `72eca87cedbf` (tree
        `b341b347574f…`);
      - code leg `opensoft/openWallet-code` at `9cabda85f8c5` (tree
        `b7eba3104569…`).

      `scaffold-project.py` carries no upstream-org guard, so no flag was
      passed; this is recorded as the operator's act, on his word.
- [x] 3.3 Verify the scaffold's `project.yaml` against `design.md` D7:
      - `elected_by: "Brett Heap"`, `elected_on: 2026-10-08`;
      - `topic: xf-project-openwallet`, `visibility: public`, `tracking_branch: main`;
      - `shape:` pinning openRepoShape by commit and `sorted-ls-tree-r-v1` tree
        digest, equal to `contracts/shape-pin.yaml`;
      - `neutral_product_pins: []`;
      - the three legs with their `naming:` records.

      Then check GitHub: `gh repo view` reads PUBLIC for all three, and each
      repository carries the topic.

      **DONE 2026-10-08**, on the three repositories as created.
      - In the assembly root, `make bootstrap` reads `bootstrap ok`: the legs
        on `main` at their pins; `manifest ok: openWallet (openwallet), 3
        legs`; both gitlinks equal `contracts/{spec,code}-pin.yaml`, the tree
        digests recomputing; the 11 copied shape files match
        `contracts/shape-pin.yaml`.
      - `project.yaml` reads `elected_by: "Brett Heap"`, `elected_on:
        2026-10-08`, `topic: xf-project-openwallet`, `visibility: public` and
        `tracking_branch: main`; `shape:` pins openRepoShape at commit
        `7f84ca42…` with `sorted-ls-tree-r-v1` tree digest `3be52767e727…`,
        equal to the shape pin; `neutral_product_pins: []`; three legs with
        `naming:` records (assembly `neutral-product`, legs `project-leg`).
      - GitHub: `gh repo view` reads PUBLIC for all three, each carrying the
        topic.
- [x] 3.4 `[openWallet-root]` The cutover runbook, authored BEFORE the carve, a
      rollback per phase written before the phase; `.specify/` bootstrapped at
      the root.
      **DONE 2026-10-08** on Brett Heap's words in session, verbatim: "start
      group 3" and "land them when green". Landed in opensoft/openWallet#1 at
      merge `2b8e223454044ba33cf371637ed536635d7f4fcf` (head `cefb918c`);
      check `validate` completed success.
      - `docs/openwallet-cutover-runbook.md`: phases 0–6, each with its
        rollback written before it. Every command was rehearsed in scratch
        clones: the carve layers of 80 (code), 38 (spec) and 10 (root) rows
        blob- and mode-identical with full history; the spec gate `3 passed`
        with the subject lines applied; a root commit passing `make
        validate`; and the three negatives OBSERVED — `pin-gitlink-mismatch`,
        an undeclared line or file refused, a mutated blob `MISMATCH`.
      - `.specify/` bootstrapped at the root: 47 files, the
        `setup-openspeckit` three-leg output, no active feature, `memory/`
        omitted as the root tracks none.
      - The leg gitlinks and `contracts/{code,spec}-pin.yaml` are untouched.
- [x] 3.5 `[openWallet]` Each repository's `README.md`, `AGENTS.md`, `CLAUDE.md`
      and `.github/CODEOWNERS`. The root's `AGENTS.md` points, beside
      `AGENTS-shape.md`, to the carve manifest's declared Q7 override.
      **DONE 2026-10-08** on Brett Heap's words in session, verbatim: "start
      group 3" and "land them when green". Landed across the three pull
      requests:
      - opensoft/openWallet#1 → `2b8e223454044ba33cf371637ed536635d7f4fcf`;
      - opensoft/openWallet-spec#1 →
        `cfd0a69cfbb78832195fd0acae4e7f4558855648`;
      - opensoft/openWallet-code#1 →
        `51b8e9c3b7beb9ecbed83529700948055e5872d7`.

      Each repository carries `README.md`, `AGENTS.md`, `CLAUDE.md` and
      `.github/CODEOWNERS`. The root's `AGENTS.md` points, beside
      `AGENTS-shape.md`, to the carve manifest's declared Q7 override at
      `docs/openwallet-carve-manifest.yaml` in openXwallet. Two declared
      exceptions were flagged on the root pull request:
      - two illustrative workspace-root example paths inside the vendored
        `.specify` overlay, which is content-addressed, so the fix is
        upstream;
      - the shape-pinned root `.gitignore` cannot take `/worktrees/`, so the
        workaround is `.git/info/exclude`.
- [x] 3.6 `[openWallet-spec]` The leg's own OpenSpec gate — RULED 2026-10-08,
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

      **DONE 2026-10-08** on Brett Heap's words in session, verbatim: "start
      group 3" and "land them when green". Landed in
      opensoft/openWallet-spec#1 at merge
      `cfd0a69cfbb78832195fd0acae4e7f4558855648` (head `9152cf11`); check
      `openspec-cli-pin-gate` completed success.
      - Committed: the tarball at the path above,
        `contracts/openspec-cli-pin.yaml`,
        `scripts/install-pinned-openspec-cli.py`,
        `scripts/validate-openspec-cli-pin.py` and
        `docs/openspec-cli-pin.md`.
      - `.github/workflows/openspec-cli-pin-gate.yml` vendored from
        openxFactory `44d8fbaf7d977668973dcd116040c9405416c2ea`,
        byte-identical except the one declared `run:` line (`--no-cache
        --tarball` at the committed path).
      - The leg's `AGENTS.md` rule 3 records the ruling as its own
        offline-gate rule.
      - `openspec/config.yaml` (`schema: spec-driven`) and nothing else under
        `openspec/`. MEASURED on 1.12.0: no `openspec/` reads
        `pin-no-target`, an empty directory `pin-report-unreadable`, and the
        config alone `Totals: 0 passed, 0 failed`. So green today is the
        empty total, not a content pass.
      - OBSERVED refusing a mutated tarball: `REFUSE pin-integrity-mismatch …
        INTEGRITY DRIFT`, exit 2.
      - `LICENSE` is not yet in the legs: it is a declared addition at 4.4.

## 4. The carve, the path-mapping proof, the first release `[openWallet]`

- [x] 4.1 The CONTROL: the eight recorded sha256s recomputed at the carve
      commit, 8/8, before anything is carved.
      - **DONE 2026-10-08**, before anything was carved. `bin/control.py` (phase
        0 of `docs/openwallet-cutover-runbook.md` in opensoft/openWallet), run
        against a fresh `--mirror --no-local` clone of opensoft/openXwallet at
        the carve commit `90111df262d6f54f7e82651d860adc12345f83f4`, printed
        `control: 8/8 owned digest(s) recomputed equal`. Re-run the same day
        with the same result.
- [x] 4.2 `[openWallet-code]` Carve the carve manifest's `openwallet_code` rows:
      `git filter-repo` from a fresh clone, one exact `--path` per row, no globs,
      no `--path-rename`, full history. Merge into the seeded leg with
      `--allow-unrelated-histories`. Blob and mode identity 100% at the carve
      layer; both `examples/` prefixes preserved.
      - **LANDED 2026-10-08** in opensoft/openWallet-code#2 at merge
        `72313daab1f229c049cb90998931564c1904dbbc` (a merge commit; parents
        `51b8e9c3` the scaffold `main` and commit B,
        `75b990dc7ea99823626c18816b37d971f46e341b`). Commit A, the pure carve
        layer, is `32c933551b92d83122a45847215d5ebe92ae6740`. Checks
        `wallet-validation` and `pytest-suite` completed success on head
        `75b990dc`.
- [x] 4.3 `[openWallet-spec]` The same for the `openwallet_spec` rows.
      - **LANDED 2026-10-08** in opensoft/openWallet-spec#2 at merge
        `15c15bbd451a803f0acdb24e5234836db829a2d3` (a merge commit; parents
        `cfd0a69c` the scaffold `main` and
        `5ea9539428eae850ba71e6f0ba8a38db061e809a` commit B). Commit A, the pure
        carve layer, is `c788cba28a81b0dc17da4cea5db1e57eceb3a193`.
- [x] 4.4 The declared-edit layer per leg, one auditable diff each.
      - Code leg: validator hunks (a)–(e); the corpus binding added (Q6); the
        `tests/nested_repo_prune/` split; `wallet-validation`'s envelope-verify
        step removed; `LICENSE` added.
      - Amended 2026-10-08, on Brett Heap's ruling "Amend the manifest: 8
        declared lines (Recommended)" (#25). The code leg's test split also
        takes `tests/multi_key_wallets/test_declared_key_sets.py` :108-111 and
        :117-118, which drop the `_grant` fixture's posture, and
        `tests/nested_repo_prune/test_prune_and_register_note.py` :47-48, the
        corpus note 21/42/11. Measured: 37 passed, 1 skipped.
      - Spec leg: the eleven subject lines; the three `openXwallet` occurrences in
        `add-composition-drift-cascade`'s deltas; `LICENSE` added.
      - **LANDED 2026-10-08**, both legs' commit B inside the merges at 4.2 and
        4.3, one auditable diff each (`git diff A B` per leg). Code leg
        measured 37 passed, 1 skipped; the spec leg's own vendored OpenSpec
        gate green. Codex did not review these pull requests: its connector
        was at its usage limit.
- [x] 4.5 `[openWallet-root]` Carve the `openwallet_root` rows and apply the
      manifest's declared field edits:
      - `carved_from:`;
      - each owned row's `path:` gaining `code/`;
      - `source_path:`;
      - the consumed hermes row removed.

      Do it in ONE root commit that also moves both gitlinks and
      `contracts/{code,spec}-pin.yaml` in lockstep. The shape's `validate` is
      green.
      - **LANDED 2026-10-08** in opensoft/openWallet#2 at merge
        `1c68717f1ae4ae132d6942f8c7f533baf292d0b6` (a merge commit). The
        lockstep commit is `b48bcb20b31dece4d582444cf01f617a799d297d`
        (parents: root `main` `2b8e2234`, the pure carve layer `3c44089c`):
        ten `openwallet_root` rows carved from the carve commit;
        `contracts/manifest.yaml` changed on its 67 declared lines only
        (`carved_from:`, eight `path:`/`source_path:` pairs now
        `code/contracts/…` and `openWallet-code/contracts/…`, the consumed
        hermes row removed); both gitlinks and `contracts/{spec,code}-pin.yaml`
        moved to spec `15c15bbd451a803f0acdb24e5234836db829a2d3` and code
        `72313daab1f229c049cb90998931564c1904dbbc`. Followed by `a51f05b6`
        (runbook helper 3 `--diff-algorithm=histogram`, helper 5
        `declared-lines-exact.py`) and `e4a7a6a9` (post-carve status in
        AGENTS.md and README). `validate` completed success on head
        `e4a7a6a9` with the real lockstep-pins step: `pins ok`. Helper 3 and
        helper 5: 0 refusals; three-way 8/8; control 8/8. Codex did not
        review: its connector was at its limit.
- [x] 4.6 `[openWallet-root]` The proof, `docs/byte-identity-<first tag>.md`,
      parts zero to five of `design.md` D7 — the DECLARED PATH MAPPING — each
      able to fail. A validator line in no declared hunk, or a path in no
      declared class, REFUSES it. Part three runs from the code leg's own root.
      - **RULED 2026-10-08**, Brett Heap, label verbatim
        "wallet-v1.6 (Recommended)" for the first root tag name, so the proof
        is `docs/byte-identity-wallet-v1.6.md`; and
        "Start now, neutrality half later (Recommended)": parts zero, one, two,
        four and five authored now by lane openXwallet-2; part three's
        composed-adapter half is filled when group 5's composed validator
        exists (lane openXwallet-3). Landed; see below.
      - **PENDING**, part three's second half: the neutrality gate over the
        composed adapter. It WAS measured, at the head `a02c6c74` of lane
        openXwallet-3's branch `rebuild/adapter-group-5` of opensoft/openXwallet
        (see the LANDED bullet below); the pinned root cited below, `1c68717f`,
        was the development pin, and the final root is `52d75736`. The shape,
        as that lane gave it: from an openXwallet checkout at that branch,
        with openWallet pinned at the root merge
        `1c68717f1ae4ae132d6942f8c7f533baf292d0b6` (its `code` gitlink
        `72313daab1f229c049cb90998931564c1904dbbc`), run
        `git submodule update --init openWallet` and
        `git -C openWallet submodule update --init code`; the composed
        validator then runs as `python3 scripts/validate-openxwallet.py <tree>
        [--strict]` (needs pyyaml, jsonschema and rfc3339-validator). The gate:
        the carve-commit validator (`scripts/validate-openxwallet.py` at
        openXwallet `90111df`) and the composed adapter print byte-identical
        output and the same exit code, plain and `--strict`, over the same
        tree, for each of this tree, the openxFactory governance export, and
        every test-suite fixture tree.
      - **LANDED 2026-10-09** in opensoft/openWallet#3 at merge
        `52d75736156550b48992e39f7a69fb680c611287` (a merge commit; head
        `6b25be50`; commits `624e196` the proof, `b86c6a5` root docs status,
        `c644bf7` the adapter-half fill, `6b25be5` the runbook 3c snippet's
        exit code). `docs/byte-identity-wallet-v1.6.md`: parts zero, one (a),
        one (b), two (a), two (b), three (both halves), four and five
        RUN-GREEN; D5's neutrality gate EMPTY plain and `--strict` over
        openXwallet's tree at `a02c6c74`, the openxFactory `governance/`
        export at `c8dde131`, and all 110 suite-built trees; consumer depth 2
        88/88; consumer depth 3 PENDING group 6; the adapter-half head is
        re-confirmed when group 5 lands; the from-text re-run finished clean
        (`runner exit=0`) and is being closed by a follow-up doc commit.
        Finding 4 (the code leg's checkout scanned in place differs by one
        `repo scan` summary line because `repo_scan` skips the validator's own
        packaged registry by resolved path) ruled "Qualify D5's sentence; gate
        stays GREEN (Recommended)" (design D5 amendment in flight). Landed on
        the word "land the proof PR when green" and the ruling "Land it now
        (Recommended)". `validate` completed success with the lockstep-pins
        step. Codex did not review.
- [ ] 4.7 **[OPERATOR]** Three rulesets, each EVALUATE → one trivial pull request
      so its checks report → ACTIVE. Each is an org-admin act in `opensoft`.
      - root: `validate`;
      - spec leg: its OpenSpec gate;
      - code leg: `wallet-validation` and `pytest-suite`.
- [x] 4.8 `[openWallet-spec]` openWallet's birth change in the leg's own
      OpenSpec instance, after 4.3 lands. It MODIFIES *Agent authority is grant
      scope, not a parallel vocabulary* to the text drafted in `design.md` D8.
      - **LANDED 2026-10-09** by lane openXwallet-1 in
        opensoft/openWallet-spec#3 at merge
        `1506bbdb4194a779bef63d8c4e5eecc7eac0bd68` (a merge commit; head
        `5f95efdd38bb177c1a8ccd94da1a1c9ef45faf3b`, two commits on the carve
        merge `15c15bb`), on Brett Heap's word in session, verbatim: "land it
        when the fixes are in and the review is clean". Claimed on #25
        2026-10-08
        (https://github.com/opensoft/openXwallet/issues/25#issuecomment-6069656258).
        Gated on the leg's named run `openspec-cli-pin` completed success for
        the exact head; an independent Opus review of `5f95efdd` read CLEAN
        after its five findings on `1cc53ce` were applied; Codex reviewed
        `1cc53ce` (no major issues) and hit its usage limit on the second
        pass. Administrator merge, author cannot self-approve.
      - The change is `openspec/changes/bind-approval-posture-vocabulary/` in
        that leg (`.openspec.yaml`, `proposal.md`, `design.md`, `tasks.md`,
        one delta), `Status: proposed`: its ratification and archive in the
        leg are the operator's acts (its tasks 1.2 and 3.1). The delta is ONE
        `## MODIFIED Requirements` block on `openxwallet-agent-profile`, the
        requirement titled character-for-character, its statement D8's two
        sentences verbatim (compared by script), three scenarios: *authority
        is carried by a grant* unchanged; *the approval vocabulary is reused,
        not duplicated* re-bulleted onto the declared binding; *no binding is
        declared, so a posture is refused rather than admitted because nothing
        forbade it* new.
      - Measured on the pinned 1.12.0: the leg's gate
        `Totals: 4 passed, 0 failed`, `OK openspec-cli-pin`; dry archive in a
        scratch copy `Totals: + 0, ~ 1, - 0, → 0` on
        `openxwallet-agent-profile` only, archiving in either order with
        `add-composition-drift-cascade` to byte-identical specs.
      - **RULED** — Brett Heap, 2026-10-09, in session, by multiple choice,
        label verbatim "Keep the promoted title, MODIFIED block
        (Recommended)": scenario two keeps the promoted title "the approval
        vocabulary is reused, not duplicated" (D8 listed it as "the bound
        vocabulary is reused, not duplicated") because 1.12.0 refuses a
        MODIFIED block that drops a scenario name the promoted spec still has;
        the one route to D8's name (RENAMED to a placeholder, REMOVED, ADDED
        under the original title, in one delta; archive `+ 1, ~ 0, - 1, → 1`)
        breaks D8's form "MODIFIES exactly one requirement" and was not taken.
        First ruled the same day as "Keep the promoted title (Recommended)" on
        the change's incomplete premise, re-presented with the measured route
        and re-ruled. Recorded on #25 and in the change's `.openspec.yaml`
        `rulings`. D8's text is not amended.
      - Observed in the code leg and not taken on (recorded in the change's
        `design.md`; carried on the code-leg follow-up list by lane
        openXwallet-2): rule (g)'s refusal message at `72313da` still names
        "the neutral job envelope" though D4 says it stops; behaviour correct
        (no binding → every posture refused, `legal terms: []`), wording
        stale.
- [ ] 4.9 **[OPERATOR]** `[openWallet-root]` First release — five coordinated
      values — on the ROOT:
      - the annotated `wallet-v*` tag on the root commit that pins both legs;
      - `contracts/manifest.yaml`, `contracts/CHANGELOG.md` and
        `contracts/releases/` at the root;
      - no leg tag;
      - the tag only after 4.6 is green;
      - the number allocated here, not before.
      - The tag NAME `wallet-v1.6` was allocated 2026-10-08 on the ruling at
        4.6. The tag itself is cut only after 4.6 is green and 4.7's rulesets
        are ACTIVE.
      - **RULED** 2026-10-09, labels verbatim "The root commit carrying the
        completed proof (Recommended)" and "Wait for the full proof
        (Recommended)": `wallet-v1.6` goes on root `main` `52d75736` (spec
        `1924500`, code `72313daa`) once 4.7's rulesets are ACTIVE. The
        root's spec pin was moved by two lockstep pull requests, on the
        rulings "Re-pin spec to 1506bbdb before the tag (Recommended)"
        (opensoft/openWallet#4 → `5a444cf2`) and "Re-pin to the archive merge
        before the tag (Recommended)" (opensoft/openWallet#5 → `bead4bd8`),
        so the first release carries 4.8 in its archived form.

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
      - Group 5 is being authored by lane openXwallet-3 on branch
        `rebuild/adapter-group-5` (claimed on #25, 2026-10-08). The FINAL root
        to pin is `52d75736156550b48992e39f7a69fb680c611287` (re-pinned once
        before that pull request lands).
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
      **Pre-performed here 2026-10-08**, in openXwallet PR #27 under Brett
      Heap's ruling on it ("Rebase drift-cascade now, then land
      (Recommended)"): the block carries the promoted sentence and scenario
      verbatim, so the change travels to openWallet already rebased and only
      the subject rewrite (4.4) remains for it there.
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

#!/usr/bin/env python3
"""
extractors/etl_run.py

Shared per-item result tracking for extractor main() entrypoints.

Every extractor's stage loop follows the same shape (EXTRACTOR_CONTRACT.md
#5): walk a list of source items — files, alerts, rows, whatever the
extractor's natural unit of partial failure is — and for each one either
produce a complete written record or contribute nothing. One bad item is
isolated and logged, not silently swallowed and not allowed to abort the
rest of the run.

Before this module existed, each extractor tracked that shape as three
loose local variables (succeeded, failed, errors) and hand-rolled the same
"print summary, dump errors to stderr, exit non-zero if anything failed"
block at the bottom of main(). That's exactly the kind of thing that
drifts silently between copies: ileapp_bridge/main.py, before this module,
printed malformed-record errors to stderr but never counted them anywhere,
so a file where every record failed to normalize still exited 0 — the
orchestrator would have recorded that stage as "succeeded" while quietly
losing data. Making success/failure/exit-code a single shared object
removes that class of drift; there's no longer a second variable an
extractor author has to remember to keep in sync by hand.

Extractors with more than one independently-failable input (e.g.
extractors/mvt_iocs/ processing alerts.json and timeline.csv separately,
per EXTRACTOR_CONTRACT.md #5's multi-input rule) build one ETLRunResult
per input and combine them with merge() before deciding the stage's exit
code — one missing/malformed input still doesn't block the other.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field


@dataclass
class ETLRunResult:
    """Accumulates per-item outcomes across one extractor stage run.

    `succeeded`/`failed` count whatever unit the extractor treats as its
    natural item of partial failure — files for crash, records for
    mvt_iocs/ileapp_bridge. An extractor that writes many rows per item
    should call ok() once per item, not once per row, so the printed
    summary answers "how many things did I process" rather than "how many
    rows exist," which is what a reader actually wants after a run.
    """

    succeeded: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def ok(self, count: int = 1) -> None:
        """Record `count` items that completed successfully."""
        self.succeeded += count

    def fail(self, item_label: str, error: BaseException | str) -> None:
        """Record one failed item. `item_label` should identify the
        specific item (filename, alert index, table name) so the printed
        error is actionable without re-running with more logging."""
        self.failed += 1
        self.errors.append(f"{item_label}: {error}")

    def note(self, message: str) -> None:
        """Record an informational message that should be surfaced but
        must NOT affect exit_code — e.g. an optional input file (like
        mvt_iocs's alerts.json) simply wasn't present for this backup.
        Distinct from fail(): a note is expected-and-handled, not a
        partial failure of the stage."""
        self.notes.append(message)

    def merge(self, other: "ETLRunResult") -> "ETLRunResult":
        """Combines two independently-tracked runs into one for a single
        exit-code decision. Used when a stage processes more than one
        input file/source independently (EXTRACTOR_CONTRACT.md #5)."""
        return ETLRunResult(
            succeeded=self.succeeded + other.succeeded,
            failed=self.failed + other.failed,
            errors=[*self.errors, *other.errors],
            notes=[*self.notes, *other.notes],
        )

    @property
    def exit_code(self) -> int:
        """0 if nothing failed, 1 otherwise — EXTRACTOR_CONTRACT.md #2:
        any failed item means the stage as a whole reports non-zero, even
        though everything that DID succeed is already durably written.
        Partial progress is never rolled back because of a later failure
        in the same run."""
        return 1 if self.failed else 0

    def print_summary(self, tag: str) -> None:
        """The `[tag] N succeeded, M failed` line plus per-error/per-note
        stderr dump every extractor's main() used to print by hand.
        `tag` is the extractor's bracketed log prefix (e.g. "crash",
        "mvt_iocs") so output stays consistent with everything else that
        extractor already prints."""
        print(f"[{tag}] {self.succeeded} succeeded, {self.failed} failed")
        for msg in self.notes:
            print(f"[{tag}]   {msg}", file=sys.stderr)
        for err in self.errors:
            print(f"[{tag}]   {err}", file=sys.stderr)

"""
extractors/etl_run.py

Per-stage ETL bookkeeping shared by every Python extractor.

Why this exists as its own module rather than a few counters in each
extractor: EXTRACTOR_CONTRACT.md §5 asks for two things that pull in
opposite directions — partial progress must survive (write rows 1–339 even
though #340 threw) *and* the stage must still exit non-zero so the
orchestrator records the failure. Hand-rolling that per extractor is how
you end up with a stage that writes nothing and exits 0, which is the one
outcome the contract exists to prevent: the run completes, the report
renders, and the domain is silently absent.

ETLRunResult makes the two facts independent and both mandatory:

    succeeded  -> how many records actually reached forensic_records
    failures   -> what didn't make it, and why, itemized

`exit_code` is derived from `failures`, never from `succeeded`. A stage that
wrote 40,000 records and lost one malformed row still exits non-zero,
because "mostly worked" is not a thing a chain-of-custody tool gets to
report as success. What makes that tolerable rather than punishing is
idempotency (§3): the re-run after a fix skips everything already ingested.

Accumulation is additive and mergeable, so the same type works at every
level of nesting — one record, one artifact file, a whole output directory —
without the caller tracking which level it is at.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

# Cap on itemized failures echoed in print_summary(). A malformed 250k-row
# CSV can fail every row; dumping all of them buries the one line the reader
# needs (the count) under noise the database already has in full.
_MAX_ITEMIZED_FAILURES = 20


@dataclass
class ETLRunResult:
    """Accumulates what a stage wrote and what it lost.

    Deliberately not a bare (int, list) tuple: the merge/exit-code/reporting
    behavior is the part that must be identical across extractors, and a
    tuple gives every caller a chance to get it subtly different.
    """

    #: Records successfully written to forensic_records.
    succeeded: int = 0

    #: (label, reason) for each unit that failed. `label` identifies the unit
    #: as precisely as the caller can — "history.csv[417]" beats "history.csv"
    #: beats "a record" when someone is trying to reproduce this later.
    failures: list[tuple[str, str]] = field(default_factory=list)

    def ok(self, written: int = 1) -> "ETLRunResult":
        """Record `written` successfully-persisted records. Returns self so
        callers can chain, but mutation is the primary interface."""
        if written < 0:
            raise ValueError(f"written must be non-negative, got {written}")
        self.succeeded += written
        return self

    def fail(self, label: str, reason: object) -> "ETLRunResult":
        """Record one failed unit.

        `reason` accepts an exception or a string. Exceptions are rendered
        with their type name, because a bare str(exc) on, say, a KeyError
        produces just `'timestamp'` — technically the message, useless as a
        diagnostic six weeks later.
        """
        if isinstance(reason, BaseException):
            rendered = f"{type(reason).__name__}: {reason}"
        else:
            rendered = str(reason)
        self.failures.append((str(label), rendered))
        return self

    def merge(self, other: "ETLRunResult") -> "ETLRunResult":
        """Combine two results into a new one. Neither input is mutated, so a
        caller can merge in a loop without the accumulator and the increment
        aliasing each other."""
        if not isinstance(other, ETLRunResult):
            raise TypeError(f"cannot merge {type(other).__name__} into ETLRunResult")
        return ETLRunResult(
            succeeded=self.succeeded + other.succeeded,
            failures=[*self.failures, *other.failures],
        )

    @property
    def failed(self) -> int:
        """Number of failed units. Named to match the `succeeded` counter it
        sits opposite, so `result.succeeded`/`result.failed` read as a pair."""
        return len(self.failures)

    @property
    def exit_code(self) -> int:
        """0 only when nothing failed.

        Derived from failures alone — never from succeeded. See module
        docstring: a stage that lost data must not be able to report success
        just because it also wrote some.
        """
        return 1 if self.failures else 0

    def print_summary(self, stage: str, stream=None) -> None:
        """Human-readable stage summary.

        Summary goes to stdout (the orchestrator captures it as run output);
        failure detail goes to stderr, because the orchestrator stores stderr
        as `pipeline_stage_status.error_message` and that is the field
        `generate_report.py` renders in the run-completeness table. A failure
        explained only on stdout never reaches the person reading the report.
        """
        print(f"[{stage}] wrote {self.succeeded} record(s); {self.failed} unit(s) failed")

        if not self.failures:
            return

        err = stream if stream is not None else sys.stderr
        shown = self.failures[:_MAX_ITEMIZED_FAILURES]
        print(f"[{stage}] {self.failed} failure(s):", file=err)
        for label, reason in shown:
            print(f"[{stage}]   - {label}: {reason}", file=err)
        remaining = self.failed - len(shown)
        if remaining > 0:
            print(f"[{stage}]   ... and {remaining} more (truncated)", file=err)

    def __bool__(self) -> bool:
        """Truthy when the stage is clean.

        Defined explicitly because the dataclass default would make an empty
        result falsy-by-field-inspection in some contexts and a
        no-work-no-failures stage is a success, not a failure.
        """
        return not self.failures

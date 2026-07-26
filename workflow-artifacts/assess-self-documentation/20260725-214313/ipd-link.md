# IPD produced by this run

- IPD: `.agents/plans/pending/20260725-2143-01-assess-self-documentation.md`
- Summary: The CLI teaches well; this plan closes the gaps. 9 proposed changes (all Low
  Remediation Risk): fix the no-args first-run EOF crash / exit-1 by gating the picker on a TTY
  and listing + exit 0 when piped (HIGH SD-01) and correct the help promise (HIGH SD-02); route
  `db info` missing-DB through the actionable `_db_not_found_error` (SD-03); make search-empty
  exit-0 intent explicit (SD-04); add `-h` examples via `epilog=` (SD-05); add a `rescope` alias
  for `filter` (SD-06); de-jargon `db rebase` help (SD-07), flesh out `filter` option help (SD-08),
  add next-steps to bare empty-result dies (SD-09). Shell completion deferred (complexity axis).
- Status at write: to-review.

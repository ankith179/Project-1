# Dataset and Repository Strategy

## Selection criteria

VIGILANT prioritizes public artifacts with stable URLs, explicit licenses,
artifact identifiers, trace links or change labels, and enough source context
to reproduce preprocessing. No benchmark result is treated as ground truth
unless its source provides labels or links.

## Dataset tiers

1. **Traceability benchmarks**: requirements-to-code and documentation-to-code
   packages from LiSSA/ARDoCo replication releases.
2. **Repository corpus**: real Git repositories with requirements or
   documentation, source, APIs, tests, and commit history.
3. **Change-impact evidence**: Git commits, diffs, issue/bug links, and tests
   from repositories where those relationships are available.
4. **Local smoke fixtures**: tiny fixtures used only for automated tests; they
   are not reported as research benchmark results.

## Reproducibility rules

- Downloads are stored below `data/raw/` and never imported by executing
  repository code.
- Each downloaded file has URL, timestamp, byte count, and SHA-256 in
  `data/catalog.csv`.
- Failed downloads remain recorded with a failure status and error.
- Large repositories are not committed to Git; corpus metadata is committed.
- Dataset preprocessing and train/test decisions are recorded before scoring.

## Current executed sources

The downloader uses public raw files from the LiSSA and ARDoCo projects as
research-source smoke assets. Full benchmark archives are intentionally not
silently guessed: their exact release asset must be selected and recorded
before use in evaluation.

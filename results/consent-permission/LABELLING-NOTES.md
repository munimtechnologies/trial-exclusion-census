# Labelling notes (consent-permission, 2026-10-30 about 16:30 UTC)

Written while labelling reading.txt (sha256 13c9e6d8b257), before key.csv or sample.json was opened.
Neither file was opened in this run. AI agents working for MV2; not yet checked by a person.

Rules applied the same way throughout, from PREREG.md:
- Adult-only trial (minimum age >= 18): any route for someone else to consent = adult_permission,
  including the WashU clause "(or that of legally authorized representative, if applicable)" and
  "a legal guardian may substitute" in an exclusion line (R097, R100).
- Trial open to minors (or ages unknown with CHILD listed): generic "parent(s)/guardian/LAR" wording
  with no word on adults = unclear (14 records, including 4 WashU-clause trials: R030 R040 R056
  R061, and R099, a prostate trial whose registry entry has no age limits). Wording tied to
  minors = minor_only. R027 counted as adult_permission because it adds "Patients with impaired
  decision-making capacity will not be excluded".
- not_a_permission: staff family-member conflict exclusions (R003 R004 R048 R081), "consent may not
  be obtained by means of a legal guardian" (R034 R051 R059), octreotide LAR (R036), surrogate
  markers (R060), exclusion of people needing proxies (R019 R077), guardian checking menarche (R093).
- R049: the excerpt was cut at 4,000 characters before the path line, so it is unclear (cannot be
  read). This is a limit of the reading file, worth noting in the result.

Totals: adult_permission 58, minor_only 15, unclear 15, not_a_permission 12, physical_only 0,
path_gone 0 (S4: all 100 still name a path).

# Plagiarism checker demo files

This folder contains 18 original, hand-written sample submissions arranged as
three independent project groups and three negative controls:

- `observatory_*` are Python samples, `garden_*` are C samples, and
  `archive_*` are JavaScript samples. They implement related but distinct
  campus-shuttle, greenhouse-watering, and event-registration programs. Each
  group has an anchor and edited variants with changed rules and additional
  features; these are not batches of generated arithmetic functions.
- The `90`, `80`, `50`, and `40` suffixes indicate the intended similarity
  range against that group's anchor. The score uses exact shared Winnowing
  fingerprints, so small code edits can shift a file between ranges.
- `independent_map.html`, `independent_glacier.sql`, and
  `independent_fieldnotes.txt` are unrelated negative controls.

## Demo steps

1. Sign in to the application and open **Document Ingestion**.
2. Select all 18 sample files (do not upload this README) and run ingestion.
3. Open **Collusion Analysis** and click **Rebuild reports for all my
   documents**. This compares every document you own, not only documents
   previously checked one at a time.
4. At `0.20` or `0.40`, the three project groups should appear as separate
   connected clusters. Increasing the threshold removes weaker links within
   each group. At `0.00`, weak cross-project overlaps can connect groups.
5. Open **Plagiarism Inspection** and check any `*_anchor` file to inspect its
   ranked matches. The match limit defaults to all candidates; you can lower
   it to inspect a smaller Top-K.

The graph also compares against documents from earlier uploads in the
account. Delete those records from **Storage Vault** or use a clean demo
account if you want to see only these clusters. Similarity ranges were checked
using the application's normalization, C++ Winnowing, and Jaccard ranking
path. Similarity alone is not proof of plagiarism or collusion.

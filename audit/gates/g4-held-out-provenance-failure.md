# Stopped G4 candidate: held-out update provenance

Date: 2026-08-13 (Asia/Calcutta)

Status: WITHDRAWN BEFORE ESTIMATION OR METRIC INSPECTION

The first G4 candidate at SHA-256
`ea8a5ccb0f11526a120900507404dc3f51ce2602bacd575aa6085f65dd97a4e6`
was stopped by independent structural review. Its predictions had the required
development-only and update-only row coverage, but all four development manifests
incorrectly recorded zero held-out update drugs and the empty-set hash. The cause was
manifest generation from the already filtered 675-row development fold file.

G3 reserves 134 update drugs. Their sorted, newline-delimited ID SHA-256 is
`8ddd245694516063bdca95c8040cfdc7d421aa3e0748d504de5f5e4ca899fdb8`.
No AUROC, performance estimate, bootstrap interval, model comparison, update result,
report, or conclusion was calculated or inspected before withdrawal.

The prospective correction derives held-out IDs as the common-complete feature IDs
minus the full 675-drug development population before any sensitivity-population
filter, requires exact equality to the G3 update-group IDs/count, writes this count and
hash into every development manifest, and makes G4 refuse a mismatch. The four
development analyses and one-time update transport must be rerun under a fresh lock;
the withdrawn G4 marker is not reusable.

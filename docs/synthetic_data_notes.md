# Synthetic Data Notes & Planted Story Threads

This document details the ground truth story threads planted in the synthetic datasets (`data/synthetic/reddy_vs_state.json` and `data/synthetic/other_cases.json`). These threads provide deterministic evaluation points for memory recall and timeline reconstruction.

---

## 1. Planted Threads in `Reddy vs. State` (`reddy-vs-state`)

### Thread A: Certified Copy Pending (`certified-copy-pending`)
- **Summary**: Court directed prosecution to produce a certified copy of bank statement (*Bank Statement — Account Ex. D-7*). The requirement remains partially unfulfilled up to Hearing 14.
- **Hearing Locations**:
  - `REDDY-H03` (2024-05-20): Document `REDDY-H03-DOC01` requested by court (`status: "pending"`). Direction `REDDY-H03-D01` issued.
  - `REDDY-H04` (2024-07-12): Adjournment `REDDY-H04-ADJ01` requested by prosecution to obtain bank statement.
  - `REDDY-H08` (2025-03-12): Direction `REDDY-H08-D01` repeated by court to submit certified bank statement.
  - `REDDY-H11` (2025-10-15): Document `REDDY-H11-DOC01` submitted as partial batch (`status: "partial"`); full certified copy remains pending.
  - `REDDY-H14` (2026-07-20): `REDDY-H03-DOC01` remains unresolved before scheduled Hearing 15 (`REDDY-H15`).

### Thread B: Electronic Evidence Certificate (`electronic-evidence-certificate`)
- **Summary**: Defence raised an objection regarding the lack of a mandatory electronic evidence certificate for digital call logs. Prosecution subsequently filed the certificate.
- **Hearing Locations**:
  - `REDDY-H08` (2025-03-12): Defence argument `REDDY-H08-A01` objecting to missing certificate. Direction `REDDY-H08-D02` issued to prosecution. Action item `REDDY-H08-ACT01` created ("Update client on outcome of certificate objection").
  - `REDDY-H10` (2025-07-22): Document `REDDY-H10-DOC01` filed by prosecution (`status: "submitted"`). Action item `REDDY-H08-ACT01` resolved (`resolved_hearing_id: "REDDY-H10"`).

### Thread C: Witness Absence Adjournment (`witness-absence-adjournment`)
- **Summary**: Witness PW-2 failed to appear at consecutive hearings, resulting in trial adjournments and re-issuance of court summons.
- **Hearing Locations**:
  - `REDDY-H05` (2024-09-08): PW-2 absent due to medical leave; adjournment `REDDY-H05-ADJ01`.
  - `REDDY-H06` (2024-11-14): PW-2 absent again; court issued fresh summons (`REDDY-H06-OUT01`).
  - `REDDY-H07` (2025-01-20): PW-2 finally examined and discharged.

### Thread D: Hearing 10 vs. Hearing 14 Differential Fact
- **Summary**: Checkable distinction in testimony progression for witness PW-3.
- **Hearing Locations**:
  - `REDDY-H10` (2025-07-22): Outcome `REDDY-H10-OUT01` notes PW-3 chief examination was deferred.
  - `REDDY-H14` (2026-07-20): Outcome `REDDY-H14-OUT01` notes PW-3 cross-examination was partly completed, with remaining cross deferred to Hearing 15.

### Thread E: Client Communication Promise
- **Summary**: Action item for defence advocate to update client on certificate objection.
- **Hearing Locations**:
  - `REDDY-H08` (2025-03-12): Created open action item `REDDY-H08-ACT01`.
  - `REDDY-H10` (2025-07-22): Resolved upon filing of electronic evidence certificate.

---

## 2. Cross-Case Comparison Datasets (`other_cases.json`)

### Case B: `Nair vs. State` (`nair-vs-state`)
- **Key Tags**: `electronic-evidence-certificate`
- **Distinguishing Strategy**: Defence filed the electronic evidence certificate with a supporting affidavit (`NAIR-H03-DOC01`), resulting in court outcome `NAIR-H04-OUT01` permitting the record to be marked.

### Case C: `Khan vs. Union Territory` (`khan-vs-union`)
- **Key Tags**: `witness-absence-adjournment`, `written-arguments`
- **Distinguishing Strategy**: Complainant witness CW-1 absent twice (`KHAN-H02`, `KHAN-H03`); court issued direction `KHAN-H04-D01` requiring concise written submissions under 5 pages.

### Case D: `Rao vs. Property Development Corp` (`rao-vs-property-corp`)
- **Distractor Case**: Civil property suit (`CS/3301/2024`). Shares **zero** issue tags with other cases to evaluate precision in semantic memory retrieval.

# Plone → PostgreSQL field mapping

**Status:** draft for review
**Owners:** STEP/CSTEP dev team (mapping) · IT (the write itself)
**Source of truth:** [`src/yc/stepcstep/db/field_map.py`](../src/yc/stepcstep/db/field_map.py)

This document is the human-readable view of `field_map.py`. If the two ever
disagree, the code wins — but they shouldn't, because
`tests/test_schema_coverage.py` fails if a form field is added without a
mapping decision, and `tests/test_field_map.py` fails on duplicate or
program-mismatched columns.

---

## 1. Scope and ownership

We produce a row; IT writes it. Nothing in this add-on opens a database
connection.

```
applicant → Plone form → submit → eligibility rules → workflow state
                                        │
                                        └→ db.serializer.to_row(obj)
                                              │
                                              └→ { column: value, ... }  → IT
```

`to_row()` returns a plain dict keyed by the column names below. The same
values, keyed by Plone field name instead, are what the eligibility rules
evaluate — one mapping, two consumers, so the decision and the stored record
can never disagree.

**Open for IT:** how the row is handed over. We recommend IT **pulls** (we
expose a read endpoint per application, IT polls or reads on demand) rather
than Plone pushing. A pull is retry-safe, needs no database credentials
inside Plone, and a failed write can't silently lose an application. If push
is preferred, we'd want a durable outbox on our side so a failed write is
retried rather than dropped. This choice does not affect any column below.

---

## 2. Table structure

Recommendation: **one `applications` table** with a `program` discriminator
and nullable program-specific columns.

- One insert path, one set of decision columns, and cross-program reporting
  is a single query — which is what the NYSED interim report needs.
- Cost: program-specific columns are nullable. Enforce correctness with
  `CHECK` constraints keyed on `program` (e.g. `program = 'cstep'` requires
  `empl_id IS NOT NULL`) rather than `NOT NULL` on the column.

The alternative — separate `step_applications` / `cstep_applications` tables —
gives cleaner constraints but doubles the reporting queries and the write
path. Not worth it at this program's scale.

The `students` table in the ER diagram should be populated **only on the
`accept` transition**, not at submit. An applicant is not a student.

### Naming

The ER diagram uses mixed case (`empl_ID`, `NYS_resident`, `application_GPA`).
PostgreSQL folds unquoted identifiers to lowercase, so those become
`empl_id`, `nys_resident`, `application_gpa` unless every reference is quoted
forever. The mapping below uses lowercase `snake_case` throughout. **Please
confirm** IT is happy to standardise on that.

---

## 3. Shared columns — both programs

| Plone field | Column | Type | PII |
|---|---|---|---|
| *(derived: Plone UID)* | `application_id` | `uuid` | |
| *(derived)* | `program` | `text` | |
| *(derived: creation date)* | `application_date` | `timestamptz` | |
| `first_name` | `first_name` | `text` | ● |
| `last_name` | `last_name` | `text` | ● |
| `date_of_birth` | `date_of_birth` | `date` | ● |
| `gender` | `gender` | `text` | |
| `ethnicity` | `ethnicity` | `text` | |
| `student_email` | `email` | `text` | ● |
| `student_phone_number` | `phone_number` | `text` | ● |
| `street_address` | `street_address` | `text` | ● |
| `apartment_number` | `apartment_number` | `text` | ● |
| `city` | `city` | `text` | |
| `state` | `state` | `text` | |
| `zip_code` | `zip_code` | `text` | |
| `nys_resident` | `nys_resident` | `boolean` | |
| `household_size` | `household_size` | `integer` | |
| `household_income` | `household_income` | `numeric(12,2)` | ● |
| `other_economic_disadvantage` | `economically_disadvantage` | `text` | |
| *(derived)* | `application_gpa` | `numeric(5,2)` | |
| *(derived)* | `gpa_scale` | `text` | |

`household_income` is **nullable by design** — an applicant may establish
economic disadvantage categorically instead of disclosing a dollar figure.

`household_size` is an integer 1–9, where **9 means "9 or more"**.

`economically_disadvantage` stores `public_assistance` or `foster_care`.

### Stored values are codes, not prose

The through-the-web form stored the entire option text as the field value —
`economically_disadvantaged` held a ~300-character paragraph. This version
stores short stable codes (`public_assistance`, `foster_care`,
`computer_science_bs`, `junior`, …) with the prose as the display label. Option
wording can then be reworded for applicants without invalidating stored rows
or breaking report queries. Full code lists are in
[`vocabularies.py`](../src/yc/stepcstep/vocabularies.py).

---

## 4. STEP-only columns (grades 7–12)

| Plone field | Column | Type | PII |
|---|---|---|---|
| `school_name` | `school_name` | `text` | |
| `current_grade` | `current_grade` | `text` | |
| `free_reduced_lunch` | `free_reduced_lunch` | `boolean` | |
| `parent1_first_name` | `parent1_first_name` | `text` | ● |
| `parent1_last_name` | `parent1_last_name` | `text` | ● |
| `parent1_email` | `parent1_email` | `text` | ● |
| `parent1_phone` | `parent1_phone` | `text` | ● |
| `parent2_first_name` | `parent2_first_name` | `text` | ● |
| `parent2_last_name` | `parent2_last_name` | `text` | ● |
| `parent2_email` | `parent2_email` | `text` | ● |
| `parent2_phone` | `parent2_phone` | `text` | ● |

Parent 1 is required, parent 2 optional. STEP applicants are minors, so
guardian contact is a legal requirement rather than a nice-to-have — worth
noting for retention and access-control decisions on these columns.

`current_grade` is stored as text (`'7'`…`'12'`) rather than an integer so it
can absorb non-numeric values later (e.g. `'ungraded'`) without a migration.

---

## 5. CSTEP-only columns (college)

| Plone field | Column | Type | PII |
|---|---|---|---|
| `emplid` | `empl_id` | `text` | ● |
| `classification` | `classification` | `text` | |
| `major` + `major_other` | `major_at_application` | `text` | |
| `degree_type` | `degree_type` | `text` | |
| `support_statement` | `statement_support` | `text` | |
| `career_aspiration` | `career_aspiration` | `text` | |
| `consent` | `consent` | `boolean` | |
| `email_consent` | `email_consent` | `boolean` | |

`major_at_application` collapses two Plone fields: it holds `major`, or the
free-text `major_other` when `major = 'other'`. `major_other` is therefore
listed in `field_map.UNMAPPED` — deliberately not its own column.

`career_aspiration` is optional. CSTEP eligibility is not limited to
applicants already majoring in a STEM field or licensed profession — an
applicant whose major is outside that list may still qualify on the strength
of an intended STEM/licensure career, and this column captures that. Which
majors qualify, and whether a stated career goal is sufficient on its own,
are not yet decided — see Q7 below.

`empl_id` is stored as text, not an integer: CUNY EMPLIDs are fixed-width
8-digit identifiers and leading zeros must survive.

---

## 6. Decision and audit columns

| Source | Column | Type |
|---|---|---|
| Plone workflow state | `status` | `text` |
| decision reason | `decision_reason` | `text` |
| decision timestamp | `decided_at` | `timestamptz` |
| rule set version | `rules_version` | `text` |

`status` takes one of: `draft`, `submitted`, `request_more_info`,
`resubmitted`, `manual_review`, `accepted`, `rejected`.

`rules_version` is the reason this section exists. Income thresholds and GPA
floors will change between program years; without recording which rule set
produced a decision, a past outcome cannot be explained to an auditor. Full
decision history (including superseded decisions from before a resubmission)
stays in Plone annotations; these four columns carry the current one.

---

## 7. Columns IT needs to add

Twenty columns in the mapping do not exist in the ER diagram, because that
diagram was drawn for CSTEP only and predates both the STEP field list and
the decision/audit requirement.

**Program discriminator (1)** — `program`

**STEP fields (12)** — `date_of_birth`, `school_name`, `current_grade`,
`free_reduced_lunch`, `parent1_first_name`, `parent1_last_name`,
`parent1_email`, `parent1_phone`, `parent2_first_name`, `parent2_last_name`,
`parent2_email`, `parent2_phone`

**Consent records (2)** — `consent`, `email_consent`

**Career goal (1)** — `career_aspiration`

`email_consent` in particular has no column today. Without it there is no
record of whether the program may contact an applicant for promotional
purposes — which is the kind of gap that only surfaces when someone
complains.

**GPA scale (1)** — `gpa_scale` (see Q4)

**Decision and audit (4)** — `status`, `decision_reason`, `decided_at`,
`rules_version`

---

## 8. PII and access control

Nineteen columns are marked ● above; `field_map.pii_columns()` returns the
list programmatically so it can drive IT's access review rather than being
transcribed by hand.

Two notes for the database side:

- `application_id` is the Plone UID, which is opaque. It is safe as a join key
  and in URLs. We deliberately do **not** derive Plone object ids from
  applicant names, so applicant identity never appears in a URL, a web server
  log, or a referrer header.
- STEP rows contain minors' contact details plus their guardians'. If row-level
  security or a restricted reporting view is on the table, these are the rows
  that need it.

---

## 9. Open questions

Q1–Q3 and Q7 change the *rules*; Q4–Q6 change the *columns*.

**Q1 — Does underrepresented-minority status establish eligibility on its
own?** CSTEP eligibility is normally "historically underrepresented minority
**or** economically disadvantaged." The decision table only tests income, so
as written it would reject a URM applicant whose household income is above
threshold. Needs the program director's answer before any reject rule ships.

**Q2 — Do the categorical indicators override the income test?** If an
applicant reports free/reduced lunch, public assistance, or foster care, does
that establish economic disadvantage regardless of the income figure? Under
NYSED rules we believe yes. As the decision table stands, an applicant on
SNAP who also reports gross income would be rejected by the "income too high"
rule.

**Q3 — Is "Clarification Statement = No" an applicant answer or a staff
judgment?** `support_statement` is required on the form, so it can never be
absent — meaning decision-table rows 3 and 5 can never fire and every such
applicant lands in Manual Review instead. Either the field becomes optional,
or "No" means *staff judged the statement inadequate*, which makes it a
reviewer input rather than an applicant field.

**Q4 — What scale is a high-school GPA on?** NYC high schools commonly report
a 0–100 average; others report 4.0. The form currently accepts 0–100 to avoid
rejecting valid input, which means `application_gpa` alone is ambiguous and
any GPA rule is unsafe. Either add a `gpa_scale` question to the STEP form
(our recommendation, and the reason the column is in the mapping) or require
one scale and state it on the form.

**Q5 — Should race and ethnicity be separate questions?** Federal and NYSED
reporting treats Hispanic/Latino ethnicity as a separate question from race,
and race as multi-select. The current single combined field cannot produce
those two report fields, and changing it later is a data migration. Cheap to
fix now; expensive after the first cohort.

**Q6 — Retention.** How long are rejected applications kept, and is there a
purge requirement? This affects whether the mapping needs a
`retention_expires_at` column.

**Q7 — Which majors count as a STEM field or licensed profession, and is
`career_aspiration` sufficient on its own?** CSTEP eligibility is normally
available either through a qualifying major or an applicant's stated intent
to pursue one. The `MAJOR` vocabulary has no STEM/non-STEM classification
today, and `career_aspiration` has no corresponding rule in
`eligibility/rules.py`. Needs the program director's list of qualifying
majors/professions before any major-based rule ships.

---

## 10. Changing this mapping

1. Edit `field_map.py` — it is plain data, no Plone imports.
2. Run `tox -e unit`. `test_schema_coverage.py` will fail if a form field has
   no mapping decision; `test_field_map.py` will fail on duplicates or
   program mismatches.
3. Update this document.
4. Send IT the diff of section 7 if columns changed.

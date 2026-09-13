# -*- coding: utf-8 -*-
"""Declarative mapping from Plone fields to PostgreSQL columns.

This module is the single source of truth for the mapping. Our team owns it;
IT owns the write itself. It deliberately imports nothing from Plone so it can
be read, diffed and unit-tested as plain data -- values for derived columns are
supplied by ``serializer.DERIVED``.

``tests/test_field_map.py`` fails if a schema field is added without either a
mapping here or an explicit entry in :data:`UNMAPPED`, so the map cannot
silently fall behind the form.
"""
from dataclasses import dataclass
from typing import Optional
from typing import Tuple


STEP = 'step'
CSTEP = 'cstep'
BOTH = (STEP, CSTEP)


@dataclass(frozen=True)
class Mapping:
    """One Plone field (or derived value) mapped to one PostgreSQL column."""

    column: str
    pg_type: str
    programs: Tuple[str, ...]
    #: Plone field name, or None when the value is derived (see DERIVED).
    field: Optional[str] = None
    #: True when the column holds personally identifiable information.
    pii: bool = False
    note: str = ''


#: Target table: applications
APPLICATIONS = (
    # --- keys and provenance -------------------------------------------
    Mapping('application_id', 'uuid', BOTH, note='Plone UID; opaque by design.'),
    Mapping('program', 'text', BOTH, note="'step' or 'cstep'."),
    Mapping('application_date', 'timestamptz', BOTH,
            note='Object creation date.'),

    # --- identity -------------------------------------------------------
    Mapping('first_name', 'text', BOTH, field='first_name', pii=True),
    Mapping('last_name', 'text', BOTH, field='last_name', pii=True),
    Mapping('date_of_birth', 'date', BOTH, field='date_of_birth', pii=True,
            note='NEW COLUMN.'),
    Mapping('gender', 'text', BOTH, field='gender'),
    Mapping('ethnicity', 'text', BOTH, field='ethnicity'),

    # --- contact --------------------------------------------------------
    Mapping('email', 'text', BOTH, field='student_email', pii=True),
    Mapping('phone_number', 'text', BOTH, field='student_phone_number',
            pii=True),
    Mapping('street_address', 'text', BOTH, field='street_address', pii=True),
    Mapping('apartment_number', 'text', BOTH, field='apartment_number',
            pii=True),
    Mapping('city', 'text', BOTH, field='city'),
    Mapping('state', 'text', BOTH, field='state'),
    Mapping('zip_code', 'text', BOTH, field='zip_code'),
    Mapping('nys_resident', 'boolean', BOTH, field='nys_resident'),

    # --- household ------------------------------------------------------
    Mapping('household_size', 'integer', BOTH, field='household_size'),
    Mapping('household_income', 'numeric(12,2)', BOTH,
            field='household_income', pii=True,
            note='Nullable: applicant may use a categorical indicator.'),
    Mapping('economically_disadvantage', 'text', BOTH,
            field='other_economic_disadvantage',
            note="Stores 'public_assistance' or 'foster_care'."),

    # --- STEP only ------------------------------------------------------
    Mapping('free_reduced_lunch', 'boolean', (STEP,),
            field='free_reduced_lunch', note='NEW COLUMN.'),
    Mapping('school_name', 'text', (STEP,), field='school_name',
            note='NEW COLUMN.'),
    Mapping('current_grade', 'text', (STEP,), field='current_grade',
            note='NEW COLUMN.'),
    Mapping('parent1_first_name', 'text', (STEP,), field='parent1_first_name',
            pii=True, note='NEW COLUMN.'),
    Mapping('parent1_last_name', 'text', (STEP,), field='parent1_last_name',
            pii=True, note='NEW COLUMN.'),
    Mapping('parent1_email', 'text', (STEP,), field='parent1_email', pii=True,
            note='NEW COLUMN.'),
    Mapping('parent1_phone', 'text', (STEP,), field='parent1_phone', pii=True,
            note='NEW COLUMN.'),
    Mapping('parent2_first_name', 'text', (STEP,), field='parent2_first_name',
            pii=True, note='NEW COLUMN.'),
    Mapping('parent2_last_name', 'text', (STEP,), field='parent2_last_name',
            pii=True, note='NEW COLUMN.'),
    Mapping('parent2_email', 'text', (STEP,), field='parent2_email', pii=True,
            note='NEW COLUMN.'),
    Mapping('parent2_phone', 'text', (STEP,), field='parent2_phone', pii=True,
            note='NEW COLUMN.'),

    # --- CSTEP only -----------------------------------------------------
    Mapping('empl_id', 'text', (CSTEP,), field='emplid', pii=True),
    Mapping('classification', 'text', (CSTEP,), field='classification'),
    Mapping('major_at_application', 'text', (CSTEP,),
            note='major, or major_other when major == "other".'),
    Mapping('degree_type', 'text', (CSTEP,), field='degree_type'),
    Mapping('statement_support', 'text', (CSTEP,), field='support_statement'),
    Mapping('consent', 'boolean', (CSTEP,), field='consent'),
    Mapping('email_consent', 'boolean', (CSTEP,), field='email_consent',
            note='NEW COLUMN. Governs whether the program may email them.'),

    # --- GPA ------------------------------------------------------------
    Mapping('application_gpa', 'numeric(5,2)', BOTH,
            note='cumulative_gpa (STEP) or gpa (CSTEP).'),
    Mapping('gpa_scale', 'text', BOTH,
            note="NEW COLUMN. '4.0' or '100'; see field_mapping.md Q4."),

    # --- decision and audit --------------------------------------------
    Mapping('status', 'text', BOTH,
            note='NEW COLUMN. The Plone workflow state.'),
    Mapping('decision_reason', 'text', BOTH, note='NEW COLUMN.'),
    Mapping('decided_at', 'timestamptz', BOTH, note='NEW COLUMN.'),
    Mapping('rules_version', 'text', BOTH,
            note='NEW COLUMN. Which rule set produced the decision.'),
)

#: Fields deliberately not written to PostgreSQL. Listing one here is a
#: decision, not an omission -- test_field_map.py requires every schema field
#: to appear either in APPLICATIONS or here.
UNMAPPED = {
    'major_other': 'Merged into major_at_application.',
}


def columns_for(program):
    """Return the mappings that apply to ``program``, in column order."""
    return tuple(m for m in APPLICATIONS if program in m.programs)


def mapped_fields():
    """Return every Plone field name that maps directly to a column."""
    return {m.field for m in APPLICATIONS if m.field}


def pii_columns():
    """Return the columns holding PII, for IT's access-control review."""
    return tuple(m.column for m in APPLICATIONS if m.pii)

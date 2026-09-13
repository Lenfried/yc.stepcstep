# -*- coding: utf-8 -*-
"""Turn an application object into the payload the rest of the system consumes.

Two outputs, one mapping:

``to_payload`` keys values by Plone field name and feeds the eligibility rules.
``to_row`` keys the same values by PostgreSQL column name and is what IT reads.

Both derive from the same object, so the rules and the database row can never
disagree about what an applicant answered.
"""
from plone import api
from plone.dexterity.utils import iterSchemata
from plone.uuid.interfaces import IUUID
from yc.stepcstep.db import field_map
from yc.stepcstep.interfaces import IEligibilityRecord
from zope.schema import getFieldsInOrder


def to_payload(obj):
    """Return every schema field value on ``obj``, keyed by field name.

    Behaviour fields are included, so adding a field to a shared behavior
    reaches the eligibility rules without touching this function.
    """
    payload = {}
    for schemata in iterSchemata(obj):
        for name, _field in getFieldsInOrder(schemata):
            payload[name] = getattr(obj, name, None)
    return payload


def _major_at_application(obj):
    major = getattr(obj, 'major', None)
    if major == 'other':
        return getattr(obj, 'major_other', None)
    return major


def _application_gpa(obj):
    if obj.program == field_map.STEP:
        return getattr(obj, 'cumulative_gpa', None)
    return getattr(obj, 'gpa', None)


def _gpa_scale(obj):
    # CSTEP collects a 4.0 GPA explicitly. STEP accepts either a 4.0 or a
    # 100-point average and cannot currently tell them apart -- see
    # docs/field_mapping.md, Q4.
    if obj.program == field_map.CSTEP:
        return '4.0'
    return None


def _created(obj):
    return obj.created().asdatetime()


def _decision(obj, key):
    latest = IEligibilityRecord(obj).latest()
    if latest is None:
        return None
    return latest.get(key)


#: Column name -> how to compute it from the object.
DERIVED = {
    'application_id': IUUID,
    'program': lambda obj: obj.program,
    'application_date': _created,
    'major_at_application': _major_at_application,
    'application_gpa': _application_gpa,
    'gpa_scale': _gpa_scale,
    'status': lambda obj: api.content.get_state(obj=obj, default=None),
    'decision_reason': lambda obj: _decision(obj, 'reason'),
    'decided_at': lambda obj: _decision(obj, 'decided_at'),
    'rules_version': lambda obj: _decision(obj, 'rules_version'),
}


def to_row(obj):
    """Return the PostgreSQL row for ``obj``, keyed by column name."""
    row = {}
    for mapping in field_map.columns_for(obj.program):
        if mapping.field:
            row[mapping.column] = getattr(obj, mapping.field, None)
        else:
            row[mapping.column] = DERIVED[mapping.column](obj)
    return row

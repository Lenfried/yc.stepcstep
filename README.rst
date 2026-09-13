============
yc.stepcstep
============

Plone 6 add-on providing the application intake for York College's STEP and
CSTEP programs.

- ``step_application`` -- Science and Technology Entry Program, grades 7-12.
- ``cstep_application`` -- Collegiate Science and Technology Entry Program,
  enrolled college students.

Both types share the applicant identity and household fields through
behaviors, and both are bound to a single ``step-cstep-application`` workflow.


How it fits together
====================

::

    applicant fills form in Plone  (draft)
              |
              |  submits
              v
    event_handlers.evaluate_application
              |
              +-- db.serializer.to_payload(obj)     one payload
              |
              +-- eligibility.rules.decide(...)     pure Python, no Plone
              |
              +-- records the decision in annotations  (immutable audit trail)
              |
              +-- fires the resulting workflow transition
                        |
                        v
        request_more_info / manual_review / accepted / rejected

The same payload feeds the eligibility rules and the PostgreSQL row, so the
rules and the database can never disagree about what an applicant answered.

Our team owns the field mapping (``src/yc/stepcstep/db/field_map.py`` and
``docs/field_mapping.md``). IT owns the write into PostgreSQL.


Current status
==============

The program's automated accept/reject criteria are **not yet defined**. Until
they are, ``eligibility/rules.py`` implements only the completeness check and
routes every complete application to ``manual_review``. Nothing is
auto-rejected. See ``docs/eligibility_rules.md`` for the open questions.


Development
===========

::

    pip install -e ".[test]" -c constraints.txt

    # full suite, needs a Plone site fixture
    zope-testrunner --all --test-path=src

    # the eligibility rules and field map import no Plone code
    tox -e unit

    tox -e lint

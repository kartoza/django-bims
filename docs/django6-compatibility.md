# Django 6 Compatibility Issues - django-bims

This document summarizes the Python packages that required modifications to work with Django 6.0.2 in the django-bims project.

## Overview

When upgrading from Django 4.x to Django 6.0.2, several third-party packages had compatibility issues. These fall into three categories:

1. **Test failures** - Package works at runtime but tests fail with Django 6
2. **Version constraints** - Package specifies `django<6.0` but works fine
3. **Code incompatibility** - Package uses removed Django APIs

---

## 1. Packages with Failing Tests

These packages work at runtime but their test suites fail with Django 6. We skip tests during the Nix build.

| Package | Version | Issue |
|---------|---------|-------|
| django-extensions | 4.1 | Tests use `CheckConstraint(check=...)` syntax; Django 5+ renamed parameter to `condition=` |
| django-ninja | 1.4.1 | `ValueError: Converter 'uuid' is already registered` - UUID URL converter conflict |
| django-modeltranslation | 0.19.14 | `MultilingualQuerySet._update()` method signature changed in Django 6 |
| django-treebeard | 4.7.1 | Migration tests fail due to Django 6 field ID changes |
| django-allauth | 65.9.0 | Tests fail due to django-ninja UUID converter issue (transitive) |
| pylint-django | 2.6.1 | Test assertions fail with Django 6 behavior changes |

---

## 2. Packages with Overly Strict Version Constraints

These packages declare `django<6.0` or similar but work correctly at runtime. We relax the version constraint.

| Package | Version | Declared Constraint | Status |
|---------|---------|---------------------|--------|
| django-timezone-field | 7.0 | `django<6.0,>=3.2` | Works at runtime |
| django-tenants | 3.10.0 | Native Django 6 support | Upgraded from 3.7.0 |
| django-easy-audit | 1.3.8 | `django<6.0,>=4.2` | Works at runtime |

---

## 3. Packages Requiring Replacement

These packages use Django APIs that were removed and cannot work with Django 6.

| Package | Version | Issue | Solution |
|---------|---------|-------|----------|
| django-cryptography | 1.1 | Uses `django.utils.baseconv` (removed in Django 5.0) | Replace with [django-cryptography-5](https://pypi.org/project/django-cryptography-5/) v2.0.3 |

---

## 4. Django 6 Dependency Issue

Django 6.0.2 itself requires `asgiref>=3.9.1`, but nixpkgs currently has version 3.8.1. We relax this constraint as it works at runtime.

---

## Recommendations

1. **Monitor upstream** - Watch for new releases of the affected packages that add official Django 6 support
2. **Test thoroughly** - Since we're skipping package tests, ensure application-level tests cover the functionality
3. **Consider alternatives** - For django-cryptography, the `-5` fork is community-maintained; consider migrating to `django-fernet-fields` or similar if long-term support is needed

---

## References

- [Django 5.0 Release Notes](https://docs.djangoproject.com/en/5.0/releases/5.0/) - Breaking changes from 4.x
- [Django 6.0 Release Notes](https://docs.djangoproject.com/en/6.0/releases/6.0/) - Breaking changes from 5.x
- [django-cryptography-5 on PyPI](https://pypi.org/project/django-cryptography-5/) - Django 5/6 compatible fork

---

*Document generated: 2026-03-17*
*Django version: 6.0.2*
*Python version: 3.12*

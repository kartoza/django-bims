# Nix Package Derivations for django-bims

This directory contains Nix derivations for Python packages that are not available
in nixpkgs. These derivations are structured to be easily upstreamed to nixpkgs.

## Directory Structure

```
nix/packages/
├── python/
│   ├── <package-name>/
│   │   └── default.nix
│   └── ...
└── README.md
```

## Included Packages

| Package | Version | Description |
|---------|---------|-------------|
| django-admin-inline-paginator | 0.4.0 | Django admin inline paginator |
| django-admin-rangefilter | 0.13.3 | Date/datetime range filter for Django admin |
| django-braces | 1.14.0 | Reusable mixins for Django |
| django-colorfield | 0.9.0 | Color field with color picker widget |
| django-contact-us | 0.4.3 | Contact us forms for Django |
| django-cryptography | 1.1 | Encryption utilities for Django |
| django-easy-audit | 1.3.8 | Audit logging with model tracking |
| django-forms-bootstrap | 3.1.0 | Bootstrap integration for Django forms |
| django-grappelli | 4.0.3 | Jazzy skin for Django Admin |
| django-imagekit | 4.0.2 | Automated image processing |
| django-invitations | 2.0.0 | Generic invitations for Django |
| django-modelsdoc | 0.1.11 | Documentation generator for Django models |
| django-ordered-model | 3.7.4 | Orderable Django models |
| django-preferences | 1.0.0 | Database-backed preferences |
| django-role-permissions | 2.2.1 | Role-based permissions |
| django-uuid-upload-path | 1.0.0 | UUID-based file upload paths |
| djangorestframework-gis | 1.0 | GIS extensions for DRF |
| dj-pagination | 2.5.0 | Pagination tools for Django |
| eutils | 0.6.0 | NCBI Entrez E-Utilities client |
| geonode-oauth-toolkit | 2.2.2 | OAuth toolkit for GeoNode |
| pygbif | 0.6.0 | GBIF API client |
| python-dwca-reader | 0.16.0 | Darwin Core Archive reader |
| raven | 6.10.0 | Legacy Sentry client (deprecated) |

## Upstreaming to nixpkgs

These derivations follow nixpkgs conventions and can be upstreamed:

1. Copy the `default.nix` to `pkgs/development/python-modules/<package-name>/default.nix`
2. Add the package to `pkgs/top-level/python-packages.nix`
3. Run the package tests: `nix build .#python3Packages.<package-name>`
4. Submit a PR to nixpkgs

### Checklist for Upstreaming

- [ ] Uses `buildPythonPackage`
- [ ] Has proper `meta` attributes (description, homepage, license)
- [ ] Has `pythonImportsCheck` for basic testing
- [ ] Dependencies are correctly specified
- [ ] Hash is verified and correct

## Using the Overlay

These packages are exposed via `nix/overlay.nix` which extends
`pythonPackagesExtensions`. The flake imports this overlay automatically.

## Updating Hashes

To update a package hash:

```bash
# For PyPI packages
nix-prefetch-url "https://files.pythonhosted.org/packages/source/p/<package>/<package>-<version>.tar.gz" --type sha256
nix hash convert --hash-algo sha256 --to sri <base32-hash>

# For GitHub packages
nix-prefetch-github <owner> <repo> --rev <tag>
```

---
Made with love by Kartoza | https://kartoza.com

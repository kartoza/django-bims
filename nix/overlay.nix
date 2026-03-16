# Python package overlay for django-bims
# These packages are not available in nixpkgs and are suitable for upstreaming
final: prev: {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
    (python-final: python-prev: {
      django-admin-inline-paginator = python-final.callPackage ./packages/python/django-admin-inline-paginator { };
      django-admin-rangefilter = python-final.callPackage ./packages/python/django-admin-rangefilter { };
      django-braces = python-final.callPackage ./packages/python/django-braces { };
      django-colorfield = python-final.callPackage ./packages/python/django-colorfield { };
      django-contact-us = python-final.callPackage ./packages/python/django-contact-us { };
      django-cryptography = python-final.callPackage ./packages/python/django-cryptography { };
      django-easy-audit = python-final.callPackage ./packages/python/django-easy-audit { };
      django-forms-bootstrap = python-final.callPackage ./packages/python/django-forms-bootstrap { };
      django-grappelli = python-final.callPackage ./packages/python/django-grappelli { };
      django-imagekit = python-final.callPackage ./packages/python/django-imagekit { };
      django-invitations = python-final.callPackage ./packages/python/django-invitations { };
      django-modelsdoc = python-final.callPackage ./packages/python/django-modelsdoc { };
      django-ordered-model = python-final.callPackage ./packages/python/django-ordered-model { };
      django-preferences = python-final.callPackage ./packages/python/django-preferences { };
      django-role-permissions = python-final.callPackage ./packages/python/django-role-permissions { };
      django-uuid-upload-path = python-final.callPackage ./packages/python/django-uuid-upload-path { };
      djangorestframework-gis = python-final.callPackage ./packages/python/djangorestframework-gis { };
      dj-pagination = python-final.callPackage ./packages/python/dj-pagination { };
      eutils = python-final.callPackage ./packages/python/eutils { };
      geonode-oauth-toolkit = python-final.callPackage ./packages/python/geonode-oauth-toolkit { };
      pygbif = python-final.callPackage ./packages/python/pygbif { };
      python-dwca-reader = python-final.callPackage ./packages/python/python-dwca-reader { };
      raven = python-final.callPackage ./packages/python/raven { };
    })
  ];
}

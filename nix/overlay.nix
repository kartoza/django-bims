# Python package overlay for django-bims
# These packages are not available in nixpkgs and are suitable for upstreaming
final: prev: {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
    (python-final: python-prev: {
      # Custom packages not in nixpkgs
      cloudnativegis = python-final.callPackage ./packages/python/cloudnativegis { };
      django-admin-inline-paginator = python-final.callPackage ./packages/python/django-admin-inline-paginator { };
      django-admin-rangefilter = python-final.callPackage ./packages/python/django-admin-rangefilter { };
      django-braces = python-final.callPackage ./packages/python/django-braces { };
      django-ckeditor = python-final.callPackage ./packages/python/django-ckeditor { };
      django-colorfield = python-final.callPackage ./packages/python/django-colorfield { };
      django-contact-us = python-final.callPackage ./packages/python/django-contact-us { };
      django-easy-audit = python-final.callPackage ./packages/python/django-easy-audit { };
      django-forms-bootstrap = python-final.callPackage ./packages/python/django-forms-bootstrap { };
      django-grappelli = python-final.callPackage ./packages/python/django-grappelli { };
      django-imagekit = python-final.callPackage ./packages/python/django-imagekit { };
      django-invitations = python-final.callPackage ./packages/python/django-invitations { };
      django-modelsdoc = python-final.callPackage ./packages/python/django-modelsdoc { };
      django-ordered-model = python-final.callPackage ./packages/python/django-ordered-model { };
      django-pipeline = python-final.callPackage ./packages/python/django-pipeline { };
      django-preferences = python-final.callPackage ./packages/python/django-preferences { };
      django-role-permissions = python-final.callPackage ./packages/python/django-role-permissions { };
      django-uuid-upload-path = python-final.callPackage ./packages/python/django-uuid-upload-path { };
      django_6 = python-final.callPackage ./packages/python/django_6 { };
      djangorestframework-gis = python-final.callPackage ./packages/python/djangorestframework-gis { };
      djangorestframework-guardian = python-final.callPackage ./packages/python/djangorestframework-guardian { };
      drf-spectacular = python-final.callPackage ./packages/python/drf-spectacular { };
      drf-spectacular-sidecar = python-final.callPackage ./packages/python/drf-spectacular-sidecar { };
      dj-pagination = python-final.callPackage ./packages/python/dj-pagination { };
      eutils = python-final.callPackage ./packages/python/eutils { };
      geonode-oauth-toolkit = python-final.callPackage ./packages/python/geonode-oauth-toolkit { };
      pygbif = python-final.callPackage ./packages/python/pygbif { };
      python-dwca-reader = python-final.callPackage ./packages/python/python-dwca-reader { };
    })
  ];
}

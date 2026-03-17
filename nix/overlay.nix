# Python package overlay for django-bims
# These packages are not available in nixpkgs and are suitable for upstreaming
final: prev: {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
    (python-final: python-prev: {
      # Override Django to use version 6
      django = python-final.callPackage ./packages/python/django_6 { };

      # Override django-extensions to skip tests (tests use Django 4 syntax)
      django-extensions = python-prev.django-extensions.overridePythonAttrs (old: {
        doCheck = false;
      });

      # Override django-ninja to skip tests (tests fail with Django 6 uuid converter)
      django-ninja = python-prev.django-ninja.overridePythonAttrs (old: {
        doCheck = false;
      });

      # Override django-modeltranslation to skip tests (API changes in Django 6)
      django-modeltranslation = python-prev.django-modeltranslation.overridePythonAttrs (old: {
        doCheck = false;
      });

      # Override django-treebeard to skip tests (migration test fails with Django 6)
      django-treebeard = python-prev.django-treebeard.overridePythonAttrs (old: {
        doCheck = false;
      });

      # Override django-timezone-field - package says <6.0 but Django 6 works
      django-timezone-field = python-prev.django-timezone-field.overridePythonAttrs (old: {
        pythonRelaxDeps = [ "django" ];
        doCheck = false;
      });

      # Override django-allauth - tests fail with Django 6 due to django-ninja uuid issue
      django-allauth = python-prev.django-allauth.overridePythonAttrs (old: {
        doCheck = false;
      });

      # Override pylint-django - tests fail with Django 6
      pylint-django = python-prev.pylint-django.overridePythonAttrs (old: {
        doCheck = false;
      });

      # Custom django-tenants 3.10.0 with Django 6 support (nixpkgs has 3.7.0)
      django-tenants = python-final.callPackage ./packages/python/django-tenants { };

      # Custom packages not in nixpkgs
      cloudnativegis = python-final.callPackage ./packages/python/cloudnativegis { };
      django-cryptography-5 = python-final.callPackage ./packages/python/django-cryptography-5 { };
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
      dj-pagination = python-final.callPackage ./packages/python/dj-pagination { };
      eutils = python-final.callPackage ./packages/python/eutils { };
      geojson-rewind = python-final.callPackage ./packages/python/geojson-rewind { };
      geomet = python-final.callPackage ./packages/python/geomet { };
      geonode-oauth-toolkit = python-final.callPackage ./packages/python/geonode-oauth-toolkit { };
      pygbif = python-final.callPackage ./packages/python/pygbif { };
      python-dwca-reader = python-final.callPackage ./packages/python/python-dwca-reader { };
    })
  ];
}

{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
}:

buildPythonPackage rec {
  pname = "django-admin-inline-paginator";
  version = "0.4.0";
  format = "setuptools";

  src = fetchPypi {
    pname = "django_admin_inline_paginator";
    inherit version;
    hash = "sha256-4VWLRo00fpZcTSW+f1RtpmguoD2VCYrje5DJJu3UkbE=";
  };

  dependencies = [ django ];

  # Tests require a Django project setup
  doCheck = false;

  pythonImportsCheck = [ "django_admin_inline_paginator" ];

  meta = with lib; {
    description = "Django admin inline paginator";
    homepage = "https://github.com/shinneider/django-admin-inline-paginator";
    license = licenses.mit;
    maintainers = with maintainers; [ ];
  };
}

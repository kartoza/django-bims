{
  lib,
  buildPythonPackage,
  fetchurl,
  django,
}:

buildPythonPackage rec {
  pname = "django-admin-inline-paginator";
  version = "0.4.0";
  format = "setuptools";

  src = fetchurl {
    url = "https://files.pythonhosted.org/packages/7e/ea/f599112f5a40d5876155aa0df8ec5013e7a1864a061323b9b7d2d675d988/django-admin-inline-paginator-0.4.0.tar.gz";
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

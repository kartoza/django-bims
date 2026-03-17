{
  lib,
  buildPythonPackage,
  fetchurl,
  setuptools,
  django,
  psycopg2,
}:

buildPythonPackage rec {
  pname = "django-tenants";
  version = "3.10.0";
  pyproject = true;

  src = fetchurl {
    url = "https://files.pythonhosted.org/packages/source/d/django_tenants/django_tenants-${version}.tar.gz";
    hash = "sha256-gaTNVGlbflYeyJ28+VImLVZDy7/DyS0YS7lpjoV8Up0=";
  };

  build-system = [ setuptools ];

  dependencies = [
    django
    psycopg2
  ];

  # Tests require database setup
  doCheck = false;

  pythonImportsCheck = [ "django_tenants" ];

  meta = with lib; {
    description = "Django tenants using PostgreSQL Schemas";
    homepage = "https://github.com/django-tenants/django-tenants";
    license = licenses.mit;
    maintainers = with maintainers; [ ];
  };
}

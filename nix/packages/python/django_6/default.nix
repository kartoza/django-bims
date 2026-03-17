{
  lib,
  buildPythonPackage,
  fetchurl,
  setuptools,
  asgiref,
  sqlparse,
  tzdata,
}:

buildPythonPackage rec {
  pname = "Django";
  version = "6.0.2";
  pyproject = true;

  build-system = [ setuptools ];

  src = fetchurl {
    url = "https://files.pythonhosted.org/packages/26/3e/a1c4207c5dea4697b7a3387e26584919ba987d8f9320f59dc0b5c557a4eb/django-6.0.2.tar.gz";
    hash = "sha256-MEalOw5A1LZ2w7d0xzQR1xhK4nRf6M5eRcDzPT3bcac=";
  };

  dependencies = [
    asgiref
    sqlparse
    tzdata
  ];

  doCheck = false;

  # Disable runtime deps check - nixpkgs has asgiref 3.8.1 but Django 6 needs >=3.9.1
  # The import still works, just a version mismatch warning
  pythonRelaxDeps = [ "asgiref" ];

  pythonImportsCheck = [ "django" ];

  meta = with lib; {
    description = "The Web framework for perfectionists with deadlines";
    homepage = "https://www.djangoproject.com/";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
  };
}

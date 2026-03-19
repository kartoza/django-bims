{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
}:

buildPythonPackage rec {
  pname = "django-modelsdoc";
  version = "0.1.11";
  format = "setuptools";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-bCkHFhmKNcq09FGeVfgbd/dtvc1Jziq6QxOvLo/Y4wg=";
  };

  dependencies = [ django ];

  doCheck = false;

  pythonImportsCheck = [ "modelsdoc" ];

  meta = with lib; {
    description = "Generate documentation for Django models";
    homepage = "https://github.com/tell-k/django-modelsdoc";
    license = licenses.mit;
    maintainers = with maintainers; [ ];
  };
}

{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
}:

buildPythonPackage rec {
  pname = "django-forms-bootstrap";
  version = "3.1.0";
  format = "setuptools";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-/8bSufugPiNmiE6C9hPa8ShHAuk0Z0bg6d4pnbgTjW8=";
  };

  dependencies = [ django ];

  doCheck = false;

  pythonImportsCheck = [ "django_forms_bootstrap" ];

  meta = with lib; {
    description = "Bootstrap integration for Django forms";
    homepage = "https://github.com/pinax/django-forms-bootstrap";
    license = licenses.mit;
    maintainers = with maintainers; [ ];
  };
}

{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
  raven,
}:

buildPythonPackage rec {
  pname = "django-sentry";
  version = "1.13.5";
  format = "setuptools";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-/RYWloYhULEQyRZ1EKdgsiw7B0w5ZY+mijQlPwfi5RE=";
  };

  dependencies = [
    django
    raven
  ];

  doCheck = false;

  pythonImportsCheck = [ "sentry" ];

  meta = with lib; {
    description = "Sentry integration for Django (legacy, use sentry-sdk)";
    homepage = "https://github.com/dcramer/django-sentry";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
  };
}

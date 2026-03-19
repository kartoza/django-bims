{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
  djangorestframework,
  django-guardian,
}:

buildPythonPackage rec {
  pname = "djangorestframework-guardian";
  version = "0.3.0";
  format = "setuptools";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-GIN1ZFLZv8wqUftOA5poN6j2aXx1ZEeqg68IV0m1kzA=";
  };

  dependencies = [
    django
    djangorestframework
    django-guardian
  ];

  doCheck = false;

  pythonImportsCheck = [ "rest_framework_guardian" ];

  meta = with lib; {
    description = "Django REST Framework permissions for Django Guardian";
    homepage = "https://github.com/rpkilby/django-rest-framework-guardian";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
  };
}

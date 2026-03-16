{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
  djangorestframework,
}:

buildPythonPackage rec {
  pname = "djangorestframework-gis";
  version = "1.0";
  format = "setuptools";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-khxa28mnwFAskFlXpmlbZ/Vde/ZYLhq4N4iLVaH85aY=";
  };

  dependencies = [
    django
    djangorestframework
  ];

  doCheck = false;

  pythonImportsCheck = [ "rest_framework_gis" ];

  meta = with lib; {
    description = "Geographic add-ons for Django REST Framework";
    homepage = "https://github.com/openwisp/django-rest-framework-gis";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
  };
}

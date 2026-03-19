{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
}:

buildPythonPackage rec {
  pname = "django-preferences";
  version = "1.0.0";
  format = "setuptools";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-FgHJMtour7Rkv8De1taTcdLGEIcKfyfIF2mlD42lIuk=";
  };

  dependencies = [ django ];

  doCheck = false;

  pythonImportsCheck = [ "preferences" ];

  meta = with lib; {
    description = "Django app providing database backed preferences";
    homepage = "https://github.com/praekelt/django-preferences";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
  };
}

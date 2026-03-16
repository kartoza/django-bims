{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
}:

buildPythonPackage rec {
  pname = "django-pipeline";
  version = "2.1.0";
  format = "setuptools";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-NqbOVv3x0IEeTVGJf1NKzKNeuzW+aZ2dD9mXDmNHkqQ=";
  };

  dependencies = [ django ];

  doCheck = false;

  pythonImportsCheck = [ "pipeline" ];

  meta = with lib; {
    description = "Asset packaging library for Django";
    homepage = "https://github.com/jazzband/django-pipeline";
    license = licenses.mit;
    maintainers = with maintainers; [ ];
  };
}

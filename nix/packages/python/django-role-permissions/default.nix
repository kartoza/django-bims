{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
}:

buildPythonPackage rec {
  pname = "django-role-permissions";
  version = "2.2.1";
  format = "setuptools";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-wA/BX2fmPL9VFLlcrrNp1glP6U11sUw6/Bu0ljur0fw=";
  };

  dependencies = [ django ];

  doCheck = false;

  pythonImportsCheck = [ "rolepermissions" ];

  meta = with lib; {
    description = "A Django app for role-based permissions";
    homepage = "https://github.com/vintasoftware/django-role-permissions";
    license = licenses.mit;
    maintainers = with maintainers; [ ];
  };
}

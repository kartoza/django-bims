{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
}:

buildPythonPackage rec {
  pname = "django-role-permissions";
  version = "3.2.0";
  format = "setuptools";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-WonqoJjz2pUbRjPmVdXzGI89bsXwuEaosWkNCU3cbqY=";
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

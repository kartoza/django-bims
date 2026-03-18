{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
  django-allauth,
}:

buildPythonPackage rec {
  pname = "django-invitations";
  version = "2.0.0";
  format = "setuptools";

  src = fetchPypi {
    pname = "django_invitations";
    inherit version;
    hash = "sha256-Sd9E/CJiNPvwitWak3hkvCj6BE4NUIs5laE1BfqgOng=";
  };

  dependencies = [
    django
    django-allauth
  ];

  doCheck = false;

  pythonImportsCheck = [ "invitations" ];

  meta = with lib; {
    description = "Generic invitations for Django";
    homepage = "https://github.com/bee-keeper/django-invitations";
    license = licenses.gpl3;
    maintainers = with maintainers; [ ];
  };
}

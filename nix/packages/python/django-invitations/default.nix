{
  lib,
  buildPythonPackage,
  fetchurl,
  django,
  django-allauth,
}:

buildPythonPackage rec {
  pname = "django-invitations";
  version = "2.0.0";
  format = "setuptools";

  src = fetchurl {
    url = "https://files.pythonhosted.org/packages/61/ea/a75be6dd366d3ef8f5dd348aa66be7352ff3f0e48a324876e40f2a6661a9/django-invitations-2.0.0.tar.gz";
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

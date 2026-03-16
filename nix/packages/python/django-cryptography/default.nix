{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
  cryptography,
}:

buildPythonPackage rec {
  pname = "django-cryptography";
  version = "1.1";
  format = "wheel";

  src = fetchPypi {
    inherit pname version;
    format = "wheel";
    python = "py2.py3";
    dist = "py2.py3";
    platform = "any";
    hash = "sha256-k3Avzw11hl1VNi8g7NlSdMTu9gzNzkbL2t4EIKzuB8s=";
  };

  dependencies = [
    django
    cryptography
  ];

  doCheck = false;

  pythonImportsCheck = [ "django_cryptography" ];

  meta = with lib; {
    description = "Easily encrypt data in Django";
    homepage = "https://github.com/georgemarshall/django-cryptography";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
  };
}

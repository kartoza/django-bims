{
  lib,
  buildPythonPackage,
  fetchFromGitHub,
  django,
}:

buildPythonPackage rec {
  pname = "django-easy-audit";
  version = "1.3.8";
  format = "setuptools";

  src = fetchFromGitHub {
    owner = "soynatan";
    repo = "django-easy-audit";
    rev = "v${version}";
    hash = "sha256-RoeiEMTMWIgxTx+VUpWxgYF5gFj2aiPlldjdJv5wtXw=";
  };

  dependencies = [ django ];

  doCheck = false;

  pythonImportsCheck = [ "easyaudit" ];

  meta = with lib; {
    description = "Django audit logging with model tracking";
    homepage = "https://github.com/soynatan/django-easy-audit";
    license = licenses.gpl3;
    maintainers = with maintainers; [ ];
  };
}

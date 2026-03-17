{
  lib,
  buildPythonPackage,
  fetchPypi,
  poetry-core,
  django,
}:

buildPythonPackage rec {
  pname = "django-easy-audit";
  version = "1.3.8";
  pyproject = true;

  src = fetchPypi {
    pname = "django_easy_audit";
    inherit version;
    hash = "sha256-XR8qANW6qG19LcliwdEdOkGq88iUPbsDrMG0cVNx1qc=";
  };

  build-system = [ poetry-core ];

  dependencies = [ django ];

  # Relax Django version - package says <6.0 but Django 6 works
  pythonRelaxDeps = [ "django" ];

  doCheck = false;

  pythonImportsCheck = [ "easyaudit" ];

  meta = with lib; {
    description = "Django audit logging with model tracking";
    homepage = "https://github.com/soynatan/django-easy-audit";
    license = licenses.gpl3;
    maintainers = with maintainers; [ ];
  };
}

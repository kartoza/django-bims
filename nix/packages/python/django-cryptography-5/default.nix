{
  lib,
  buildPythonPackage,
  fetchurl,
  setuptools,
  django,
  cryptography,
  django-appconf,
  typing-extensions,
}:

buildPythonPackage rec {
  pname = "django-cryptography-5";
  version = "2.0.3";
  pyproject = true;

  src = fetchurl {
    url = "https://files.pythonhosted.org/packages/ae/8b/214ea0d3726eeb99654213aae57463f38b2b82b3e10a746df35bd8361656/django_cryptography_5-2.0.3.tar.gz";
    hash = "sha256-9OFAqTOeFHhf1sLLuDbDcNzQAJknkYH7mLACco291j4=";
  };

  build-system = [ setuptools ];

  dependencies = [
    django
    cryptography
    django-appconf
    typing-extensions
  ];

  # Relax Django version constraint for Django 6
  pythonRelaxDeps = [ "django" ];

  doCheck = false;

  pythonImportsCheck = [ "django_cryptography" ];

  meta = with lib; {
    description = "Django field encryption using cryptography (Django 5+ compatible fork)";
    homepage = "https://github.com/vitaliyf/django-cryptography";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
  };
}

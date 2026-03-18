{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
}:

buildPythonPackage rec {
  pname = "django-braces";
  version = "1.14.0";
  format = "setuptools";

  src = fetchPypi {
    pname = "django_braces";
    inherit version;
    hash = "sha256-m7Y5Rh5FnNcC90r7HfPwpmxHMT1Svz6tgGdJoE8lsLc=";
  };

  dependencies = [ django ];

  doCheck = false;

  pythonImportsCheck = [ "braces" ];

  meta = with lib; {
    description = "Reusable, generic mixins for Django";
    homepage = "https://github.com/brack3t/django-braces";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
  };
}

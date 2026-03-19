{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
}:

buildPythonPackage rec {
  pname = "django-ordered-model";
  version = "3.7.4";
  format = "setuptools";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-8li5diUlwApTAJ6C+Li/KjqjFei0U+KB6P27/iuMs7o=";
  };

  dependencies = [ django ];

  doCheck = false;

  pythonImportsCheck = [ "ordered_model" ];

  meta = with lib; {
    description = "Allows Django models to be ordered";
    homepage = "https://github.com/django-ordered-model/django-ordered-model";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
  };
}

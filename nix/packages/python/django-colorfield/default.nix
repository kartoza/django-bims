{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
  pillow,
}:

buildPythonPackage rec {
  pname = "django-colorfield";
  version = "0.9.0";
  format = "setuptools";

  src = fetchPypi {
    pname = "django_colorfield";
    inherit version;
    hash = "sha256-II4E2uZp7ZXxjErvAoZenHhYc1If++W0b7bqehUAyXk=";
  };

  dependencies = [
    django
    pillow
  ];

  doCheck = false;

  pythonImportsCheck = [ "colorfield" ];

  meta = with lib; {
    description = "Color field for Django models with color picker widget";
    homepage = "https://github.com/fabiocaccamo/django-colorfield";
    license = licenses.mit;
    maintainers = with maintainers; [ ];
  };
}

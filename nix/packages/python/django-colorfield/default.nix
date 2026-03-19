{
  lib,
  buildPythonPackage,
  fetchurl,
  django,
  pillow,
}:

buildPythonPackage rec {
  pname = "django-colorfield";
  version = "0.9.0";
  format = "setuptools";

  src = fetchurl {
    url = "https://files.pythonhosted.org/packages/0c/6b/05218ad57d82852d13ab8243cf45047680c4cab632893a6acc3ac1ae24ea/django-colorfield-0.9.0.tar.gz";
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

{
  lib,
  buildPythonPackage,
  fetchurl,
  django,
}:

buildPythonPackage rec {
  pname = "django-braces";
  version = "1.14.0";
  format = "setuptools";

  src = fetchurl {
    url = "https://files.pythonhosted.org/packages/e5/c3/4e3c4296ce085ad570278aa8cc4b7958553bff9ef8f1f2abb93ebd303cbe/django-braces-1.14.0.tar.gz";
    hash = "sha256-g3BbeJSN4AgEv6z0DDFdABuzljDzW73YWIIRwtW01D8=";
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

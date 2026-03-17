{
  lib,
  buildPythonPackage,
  fetchurl,
  django,
}:

buildPythonPackage rec {
  pname = "django-contact-us";
  version = "0.4.3";
  format = "setuptools";

  src = fetchurl {
    url = "https://files.pythonhosted.org/packages/96/1a/f1897201d8d3b83f7ed8b12d6e6a3c3bcf96c713fe50fc8355f7d03b2290/django-contact-us-0.4.3.tar.gz";
    hash = "sha256-IxC1yyFyagY0xOJRc9K0oeX6I18KxzSc4p/2R2R/EKI=";
  };

  dependencies = [ django ];

  doCheck = false;

  pythonImportsCheck = [ "contactus" ];

  meta = with lib; {
    description = "A Django application for contact us forms";
    homepage = "https://github.com/dldevinc/django-contact-us";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
  };
}

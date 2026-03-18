{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
}:

buildPythonPackage rec {
  pname = "django-contact-us";
  version = "0.4.3";
  format = "setuptools";

  src = fetchPypi {
    pname = "django_contact_us";
    inherit version;
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

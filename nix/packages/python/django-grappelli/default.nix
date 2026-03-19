{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
}:

buildPythonPackage rec {
  pname = "django-grappelli";
  version = "4.0.3";
  format = "setuptools";

  src = fetchPypi {
    pname = "django_grappelli";
    inherit version;
    hash = "sha256-kPUyR9UaWIoFU1Y/2FtmILazDE95aYYOwyW/uXwmCd8=";
  };

  dependencies = [ django ];

  doCheck = false;

  pythonImportsCheck = [ "grappelli" ];

  meta = with lib; {
    description = "A jazzy skin for the Django Admin-Interface";
    homepage = "https://github.com/sehmaschine/django-grappelli";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
  };
}

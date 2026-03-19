{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
}:

buildPythonPackage rec {
  pname = "django-admin-rangefilter";
  version = "0.13.3";
  format = "setuptools";

  src = fetchPypi {
    pname = "django_admin_rangefilter";
    inherit version;
    hash = "sha256-gVG4QHU+osTemWOxkEy75+eGt7wE3l29ZFZ8htKHu+g=";
  };

  dependencies = [ django ];

  doCheck = false;

  pythonImportsCheck = [ "rangefilter" ];

  meta = with lib; {
    description = "Django admin filter for date and datetime fields";
    homepage = "https://github.com/silentsokolov/django-admin-rangefilter";
    license = licenses.mit;
    maintainers = with maintainers; [ ];
  };
}

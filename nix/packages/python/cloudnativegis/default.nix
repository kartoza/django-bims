{
  lib,
  buildPythonPackage,
  fetchFromGitHub,
  django,
  djangorestframework,
  psycopg2,
}:

buildPythonPackage rec {
  pname = "cloudnativegis";
  version = "0.0.5bims";
  format = "setuptools";

  src = fetchFromGitHub {
    owner = "kartoza";
    repo = "CloudNativeGIS";
    rev = version;
    hash = "sha256-sCz6ncryHhhpNLh6y8YDHtVyVOtrPb7QfyhD5lipZZk=";
  };

  dependencies = [
    django
    djangorestframework
    psycopg2
  ];

  doCheck = false;

  pythonImportsCheck = [ "cloud_native_gis" ];

  meta = with lib; {
    description = "Cloud Native GIS utilities for Django";
    homepage = "https://github.com/kartoza/CloudNativeGIS";
    license = licenses.gpl3;
    maintainers = with maintainers; [ ];
  };
}

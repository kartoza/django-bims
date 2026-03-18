{
  lib,
  buildPythonPackage,
  fetchFromGitHub,
  django,
  oauthlib,
  requests,
}:

buildPythonPackage rec {
  pname = "geonode-oauth-toolkit";
  version = "2.2.2";
  format = "setuptools";

  src = fetchFromGitHub {
    owner = "GeoNode";
    repo = "geonode-oauth-toolkit";
    rev = "v${version}";
    hash = "sha256-GtiaGLHqIRDg/BZQ61RLYfY4CoysDXCE89W7MIA/oH8=";
  };

  dependencies = [
    django
    oauthlib
    requests
  ];

  doCheck = false;

  pythonImportsCheck = [ "oauth2_provider" ];

  meta = with lib; {
    description = "OAuth toolkit for GeoNode";
    homepage = "https://github.com/GeoNode/geonode-oauth-toolkit";
    license = licenses.bsd2;
    maintainers = with maintainers; [ ];
  };
}

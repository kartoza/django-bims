{
  lib,
  buildPythonPackage,
  fetchPypi,
  requests,
  requests-cache,
  appdirs,
  matplotlib,
  geojson,
  geojson-rewind,
  geomet,
}:

buildPythonPackage rec {
  pname = "pygbif";
  version = "0.6.6";
  format = "setuptools";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-m0aiSTFMe8V1pRFChwAQhATgRZvQi5eJ1Ot5PtkL0nY=";
  };

  dependencies = [
    requests
    requests-cache
    appdirs
    matplotlib
    geojson
    geojson-rewind
    geomet
  ];

  doCheck = false;

  pythonImportsCheck = [ "pygbif" ];

  meta = with lib; {
    description = "Python client for GBIF API";
    homepage = "https://github.com/gbif/pygbif";
    license = licenses.mit;
    maintainers = with maintainers; [ ];
  };
}

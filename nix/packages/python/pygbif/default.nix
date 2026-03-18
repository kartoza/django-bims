{
  lib,
  buildPythonPackage,
  fetchPypi,
  requests,
  appdirs,
  matplotlib,
  geojson,
}:

buildPythonPackage rec {
  pname = "pygbif";
  version = "0.6.0";
  format = "setuptools";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-b2exVJ95wW9PSTrqwKZa+PIywuCsu6OUEQu47ICR2U8=";
  };

  dependencies = [
    requests
    appdirs
    matplotlib
    geojson
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

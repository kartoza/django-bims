{
  lib,
  buildPythonPackage,
  fetchPypi,
  setuptools,
  lxml,
  requests,
}:

buildPythonPackage rec {
  pname = "eutils";
  version = "0.6.0";
  format = "wheel";

  src = fetchPypi {
    inherit pname version;
    format = "wheel";
    python = "py2.py3";
    hash = "sha256-STjEuv9spSFBIE/z7/OpHsHoPlKmxdkucWNYURe5ZWY=";
  };

  dependencies = [
    setuptools  # Required for pkg_resources at runtime
    lxml
    requests
  ];

  doCheck = false;

  pythonImportsCheck = [ "eutils" ];

  meta = with lib; {
    description = "Python client for NCBI Entrez E-Utilities";
    homepage = "https://github.com/biocommons/eutils";
    license = licenses.asl20;
    maintainers = with maintainers; [ ];
  };
}

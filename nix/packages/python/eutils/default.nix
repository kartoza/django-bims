{
  lib,
  buildPythonPackage,
  fetchPypi,
  lxml,
  requests,
}:

buildPythonPackage rec {
  pname = "eutils";
  version = "0.6.0";
  format = "setuptools";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-NRUXjAqtuDYgaj7uK8nzQPMhPBO1NjLgWOtYqSGdA88=";
  };

  dependencies = [
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

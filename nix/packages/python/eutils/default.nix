{
  lib,
  buildPythonPackage,
  fetchPypi,
  lxml,
  requests,
  setuptools,
  setuptools-scm,
}:

buildPythonPackage rec {
  pname = "eutils";
  version = "0.6.0";
  pyproject = true;

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-NRUXjAqtuDYgaj7uK8nzQPMhPBO1NjLgWOtYqSGdA88=";
  };

  build-system = [
    setuptools
    setuptools-scm
  ];

  dependencies = [
    lxml
    requests
  ];

  doCheck = false;

  # Set version for setuptools_scm since we're using a release tarball
  SETUPTOOLS_SCM_PRETEND_VERSION = version;

  pythonImportsCheck = [ "eutils" ];

  meta = with lib; {
    description = "Python client for NCBI Entrez E-Utilities";
    homepage = "https://github.com/biocommons/eutils";
    license = licenses.asl20;
    maintainers = with maintainers; [ ];
  };
}

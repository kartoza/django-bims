{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
  setuptools,
}:

buildPythonPackage rec {
  pname = "drf-spectacular-sidecar";
  version = "2026.3.1";
  pyproject = true;

  src = fetchPypi {
    pname = "drf_spectacular_sidecar";
    inherit version;
    hash = "sha256-W3/trWbjhR8vRCSAeSwIEV15IXlZ0BZFuT09IliTi+E=";
  };

  build-system = [ setuptools ];

  dependencies = [
    django
  ];

  doCheck = false;

  # Skip imports check as it needs Django settings
  dontCheckPython = true;

  meta = with lib; {
    description = "Serve self-contained distribution builds of Swagger UI and Redoc for drf-spectacular";
    homepage = "https://github.com/tfranzel/drf-spectacular-sidecar";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
  };
}

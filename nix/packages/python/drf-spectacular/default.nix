{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
  djangorestframework,
  uritemplate,
  pyyaml,
  jsonschema,
  inflection,
  setuptools,
}:

buildPythonPackage rec {
  pname = "drf-spectacular";
  version = "0.29.0";
  pyproject = true;

  src = fetchPypi {
    pname = "drf_spectacular";
    inherit version;
    hash = "sha256-CgaTOeo5DOfxSnXota9KCGCkboM/1K8CdBGj6U/BoMw=";
  };

  build-system = [ setuptools ];

  dependencies = [
    django
    djangorestframework
    uritemplate
    pyyaml
    jsonschema
    inflection
  ];

  doCheck = false;

  # Skip imports check as it needs Django settings
  dontCheckPython = true;

  meta = with lib; {
    description = "Sane and flexible OpenAPI 3 schema generation for Django REST framework";
    homepage = "https://github.com/tfranzel/drf-spectacular";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
  };
}

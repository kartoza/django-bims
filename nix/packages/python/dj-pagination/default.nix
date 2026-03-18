{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
}:

buildPythonPackage rec {
  pname = "dj-pagination";
  version = "2.5.0";
  format = "setuptools";

  src = fetchPypi {
    pname = "dj_pagination";
    inherit version;
    hash = "sha256-hgMBzcee3AcSAIkhA3sjQScdOlVYa8NPrQcudMjoAMQ=";
  };

  dependencies = [ django ];

  doCheck = false;

  pythonImportsCheck = [ "dj_pagination" ];

  meta = with lib; {
    description = "Django pagination tools";
    homepage = "https://github.com/pydanny/dj-pagination";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
  };
}

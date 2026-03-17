{
  lib,
  buildPythonPackage,
  fetchurl,
  django,
}:

buildPythonPackage rec {
  pname = "dj-pagination";
  version = "2.5.0";
  format = "setuptools";

  src = fetchurl {
    url = "https://files.pythonhosted.org/packages/85/a3/74312334efdc0665ea40acaf1f0fa8d8a6a5acbc67ebf07e38a55be93ad7/dj-pagination-2.5.0.tar.gz";
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

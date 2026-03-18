{
  lib,
  buildPythonPackage,
  fetchPypi,
}:

buildPythonPackage rec {
  pname = "raven";
  version = "6.10.0";
  format = "setuptools";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-P6bebvokk6fIJ0cumEzpsCB5fQ2hbx22cZe8wjyPrlQ=";
  };

  doCheck = false;

  pythonImportsCheck = [ "raven" ];

  meta = with lib; {
    description = "Legacy Python client for Sentry (deprecated, use sentry-sdk)";
    homepage = "https://github.com/getsentry/raven-python";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
  };
}

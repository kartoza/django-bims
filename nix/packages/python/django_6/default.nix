{
  lib,
  buildPythonPackage,
  fetchPypi,
  asgiref,
  sqlparse,
  tzdata,
}:

buildPythonPackage rec {
  pname = "Django";
  version = "6.0.2";
  format = "setuptools";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-MEalOw5A1LZ2w7d0xzQR1xhK4nRf6M5eRcDzPT3bcac=";
  };

  dependencies = [
    asgiref
    sqlparse
    tzdata
  ];

  doCheck = false;

  pythonImportsCheck = [ "django" ];

  meta = with lib; {
    description = "The Web framework for perfectionists with deadlines";
    homepage = "https://www.djangoproject.com/";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
  };
}

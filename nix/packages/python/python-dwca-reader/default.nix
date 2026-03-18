{
  lib,
  buildPythonPackage,
  fetchPypi,
}:

buildPythonPackage rec {
  pname = "python-dwca-reader";
  version = "0.16.0";
  format = "setuptools";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-nQy+u6k5DAvnQDw4IJyakrPoWjOAjY3cN0uXfURgSDo=";
  };

  doCheck = false;

  pythonImportsCheck = [ "dwca" ];

  meta = with lib; {
    description = "Python reader for Darwin Core Archive files";
    homepage = "https://github.com/BelgianBiodiversityPlatform/python-dwca-reader";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
  };
}

{
  lib,
  buildPythonPackage,
  fetchurl,
  click,
}:

buildPythonPackage rec {
  pname = "geomet";
  version = "1.1.0";
  format = "wheel";

  src = fetchurl {
    url = "https://files.pythonhosted.org/packages/af/90/3bc780df088d439714af8295196a4332a26559ae66fd99865e36f92efa9e/geomet-1.1.0-py3-none-any.whl";
    hash = "sha256-Q3L+TihqNKzG8ukwgoSFC9jEqlvBIGXiq71JlZANsS8=";
  };

  dependencies = [ click ];

  doCheck = false;

  pythonImportsCheck = [ "geomet" ];

  meta = with lib; {
    description = "GeoJSON <-> WKT/WKB conversion utilities";
    homepage = "https://github.com/geomet/geomet";
    license = licenses.asl20;
    maintainers = with maintainers; [ ];
  };
}

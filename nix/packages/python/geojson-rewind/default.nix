{
  lib,
  buildPythonPackage,
  fetchurl,
}:

buildPythonPackage rec {
  pname = "geojson-rewind";
  version = "1.1.0";
  format = "wheel";

  src = fetchurl {
    url = "https://files.pythonhosted.org/packages/b1/2a/a977adbc9c1b2970ed76a6959c0087322f963d2f4f5b2dd5007d9082c00f/geojson_rewind-1.1.0-py3-none-any.whl";
    hash = "sha256-64mYkhD1M8d5dVP89hwMrN+9JHeQgSoOE6xW7EVOoTU=";
  };

  doCheck = false;

  pythonImportsCheck = [ "geojson_rewind" ];

  meta = with lib; {
    description = "A Python library for reordering GeoJSON coordinates";
    homepage = "https://github.com/chris48s/geojson-rewind";
    license = licenses.mit;
    maintainers = with maintainers; [ ];
  };
}

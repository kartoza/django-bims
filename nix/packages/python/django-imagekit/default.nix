{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
  pillow,
  pilkit,
  django-appconf,
}:

buildPythonPackage rec {
  pname = "django-imagekit";
  version = "4.0.2";
  format = "setuptools";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-bsCvt3zfUs1FPJ/CwQ7zUNER7f1s5TxZd6qKDiLO4Aw=";
  };

  dependencies = [
    django
    pillow
    pilkit
    django-appconf
  ];

  doCheck = false;

  # Import requires Django settings to be configured
  dontUsePythonImportsCheck = true;

  meta = with lib; {
    description = "Automated image processing for Django";
    homepage = "https://github.com/matthewwithanm/django-imagekit";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
  };
}

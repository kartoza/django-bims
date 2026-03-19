{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
  django-js-asset,
  pillow,
}:

buildPythonPackage rec {
  pname = "django-ckeditor";
  version = "6.6.1";
  format = "setuptools";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-qASpgTcFjAD8CSqvxHXpSRssp8aMhNbKEsT6JFNpYBc=";
  };

  dependencies = [
    django
    django-js-asset
    pillow
  ];

  doCheck = false;

  pythonImportsCheck = [ "ckeditor" ];

  meta = with lib; {
    description = "Django admin CKEditor integration";
    homepage = "https://github.com/django-ckeditor/django-ckeditor";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
  };
}

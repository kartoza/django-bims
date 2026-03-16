{
  lib,
  buildPythonPackage,
  fetchPypi,
  django,
}:

buildPythonPackage rec {
  pname = "django-uuid-upload-path";
  version = "1.0.0";
  format = "setuptools";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-mfg6F3moi+0SqwbKnr1miWD7gthmD6/hVmZbbBTs2DE=";
  };

  dependencies = [ django ];

  doCheck = false;

  pythonImportsCheck = [ "uuid_upload_path" ];

  meta = with lib; {
    description = "Generate UUIDs for Django file upload paths";
    homepage = "https://github.com/etianen/django-uuid-upload-path";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
  };
}

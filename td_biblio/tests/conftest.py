import os.path
import pytest


FIXTURES_PATH = os.path.abspath(
    os.path.dirname(__file__) + '/fixtures'
)


@pytest.fixture
def bibtex(request):
    request.cls.bibtex = os.path.join(FIXTURES_PATH, 'biblio.bib')

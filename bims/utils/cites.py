import requests
from django.conf import settings


class CitesSpeciesPlusAPI:
    def __init__(self, base_url="https://api.speciesplus.net/api/v1"):
        self.base_url = base_url
        self.headers = {
            "X-Authentication-Token": settings.CITES_TOKEN_API
        }

    def _get(self, url, params=None):
        """General GET request handler."""
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_cites_legislation(self, taxon_concept_id, params=None):
        """Get CITES legislation for a given taxon concept."""
        url = f"{self.base_url}/taxon_concepts/{taxon_concept_id}/cites_legislation"
        return self._get(url, params=params)

    def get_distributions(self, taxon_concept_id, params=None):
        """Get distributions for a given taxon concept."""
        url = f"{self.base_url}/taxon_concepts/{taxon_concept_id}/distributions"
        return self._get(url, params=params)

    def get_eu_legislation(self, taxon_concept_id, params=None):
        """Get EU legislation for a given taxon concept."""
        url = f"{self.base_url}/taxon_concepts/{taxon_concept_id}/eu_legislation"
        return self._get(url, params=params)

    def get_references(self, taxon_concept_id, params=None):
        """Get references for a given taxon concept."""
        url = f"{self.base_url}/taxon_concepts/{taxon_concept_id}/references"
        return self._get(url, params=params)

    def list_taxon_concepts(self, params=None):
        """List taxon concepts."""
        url = f"{self.base_url}/taxon_concepts.json"
        return self._get(url, params=params)

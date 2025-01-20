import requests
from django.conf import settings


class TaxonWorksClient:
    """
    A client for interacting with the TaxonWorks API.
    """
    def __init__(self,
                 user_token=None,
                 project_token=None,
                 taxonworks_domain=None):
        """
        Initialize the TaxonWorksClient with either provided credentials
        or fallback to Django settings.
        """
        self.user_token = user_token or settings.TAXONWORKS_USER_TOKEN
        self.project_token = project_token or settings.TAXONWORKS_PROJECT_TOKEN
        self.taxonworks_domain = taxonworks_domain or settings.TAXONWORKS_DOMAIN

        # Construct the base URL
        self.api_url = f'{self.taxonworks_domain}/api/v1/taxon_names'

    def fetch_taxon_names(self, max_page=10, per_page=1000):
        """
        Fetch taxon names from TaxonWorks, across multiple pages if desired.

        :param max_page: The maximum page number to fetch (inclusive).
        :param per_page: The number of records per page (default: 1000).
        :return: A list of taxon names (dicts).
        """
        headers = {
            'Authorization': f'Token {self.user_token}',
            'Content-Type': 'application/json',
        }
        params = {
            'project_token': self.project_token,
            'per': per_page,
            'page': 1,
        }

        all_taxon_names = []

        while params['page'] <= max_page:
            response = requests.get(
                self.api_url, headers=headers, params=params)
            if response.status_code == 200:
                taxon_names = response.json()
                all_taxon_names.extend(taxon_names)
                params['page'] += 1
            else:
                # Log or handle errors as needed
                print(f'Error: {response.status_code} - {response.text}')
                break

        return all_taxon_names

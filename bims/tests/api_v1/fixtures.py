# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Fixtures for API v1 tests.

Made with love by Kartoza | https://kartoza.com
"""
import pytest
from django.contrib.gis.geos import Point
from django.utils import timezone
from rest_framework.test import APIClient

from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
    IUCNStatusF,
    LocationSiteF,
    LocationTypeF,
    SurveyF,
    TaxonomyF,
    TaxonGroupF,
    UserF,
    SourceReferenceF,
    BoundaryF,
    BoundaryTypeF,
    EndemismF,
)


class APITestFixtures:
    """Base class providing fixtures for API tests."""

    @classmethod
    def create_user(cls, username='testuser', is_staff=False, is_superuser=False):
        """Create a test user."""
        return UserF(
            username=username,
            email=f'{username}@example.com',
            is_staff=is_staff,
            is_superuser=is_superuser,
        )

    @classmethod
    def create_staff_user(cls, username='staffuser'):
        """Create a staff user."""
        return cls.create_user(username=username, is_staff=True)

    @classmethod
    def create_superuser(cls, username='superuser'):
        """Create a superuser."""
        return cls.create_user(username=username, is_staff=True, is_superuser=True)

    @classmethod
    def create_api_client(cls, user=None):
        """Create an API client, optionally authenticated."""
        client = APIClient()
        if user:
            client.force_authenticate(user=user)
        return client

    @classmethod
    def create_location_type(cls, name='River'):
        """Create a location type."""
        return LocationTypeF(name=name)

    @classmethod
    def create_location_site(cls, **kwargs):
        """Create a location site with sensible defaults."""
        defaults = {
            'name': 'Test Site',
            'site_code': 'TEST001',
            'latitude': -28.5,
            'longitude': 24.5,
            'geometry_point': Point(24.5, -28.5, srid=4326),
            'validated': True,
        }
        defaults.update(kwargs)
        return LocationSiteF(**defaults)

    @classmethod
    def create_iucn_status(cls, category='LC', sensitive=False):
        """Create an IUCN status."""
        return IUCNStatusF(category=category, sensitive=sensitive)

    @classmethod
    def create_endemism(cls, name='Endemic'):
        """Create an endemism record."""
        return EndemismF(name=name)

    @classmethod
    def create_taxonomy(cls, **kwargs):
        """Create a taxonomy record."""
        defaults = {
            'scientific_name': 'Barbus anoplus',
            'canonical_name': 'Barbus anoplus',
            'rank': 'SPECIES',
            'validated': True,
        }
        defaults.update(kwargs)
        return TaxonomyF(**defaults)

    @classmethod
    def create_taxon_group(cls, name='Fish', category='Freshwater'):
        """Create a taxon group."""
        return TaxonGroupF(name=name, category=category)

    @classmethod
    def create_survey(cls, site=None, **kwargs):
        """Create a survey (site visit)."""
        if site is None:
            site = cls.create_location_site()
        defaults = {
            'site': site,
            'date': timezone.now().date(),
            'validated': True,
        }
        defaults.update(kwargs)
        return SurveyF(**defaults)

    @classmethod
    def create_biological_record(cls, site=None, taxonomy=None, survey=None, **kwargs):
        """Create a biological collection record."""
        if site is None:
            site = cls.create_location_site()
        if taxonomy is None:
            taxonomy = cls.create_taxonomy()
        if survey is None:
            survey = cls.create_survey(site=site)

        defaults = {
            'site': site,
            'taxonomy': taxonomy,
            'survey': survey,
            'collection_date': timezone.now().date(),
            'validated': True,
        }
        defaults.update(kwargs)
        return BiologicalCollectionRecordF(**defaults)

    @classmethod
    def create_source_reference(cls, **kwargs):
        """Create a source reference."""
        return SourceReferenceF(**kwargs)

    @classmethod
    def create_boundary(cls, **kwargs):
        """Create a boundary."""
        return BoundaryF(**kwargs)

    @classmethod
    def create_boundary_type(cls, name='Province'):
        """Create a boundary type."""
        return BoundaryTypeF(name=name)


class APITestDataSet:
    """Provides a complete test dataset for API tests."""

    def __init__(self):
        self.users = {}
        self.sites = []
        self.taxa = []
        self.records = []
        self.surveys = []
        self.taxon_groups = []

    def setup(self):
        """Set up complete test data."""
        # Create users
        self.users['regular'] = APITestFixtures.create_user(username='regular_user')
        self.users['staff'] = APITestFixtures.create_staff_user(username='staff_user')
        self.users['superuser'] = APITestFixtures.create_superuser(username='super_user')

        # Create taxon groups
        fish_group = APITestFixtures.create_taxon_group(name='Fish', category='Freshwater')
        invert_group = APITestFixtures.create_taxon_group(name='Invertebrates', category='Freshwater')
        self.taxon_groups = [fish_group, invert_group]

        # Create IUCN statuses
        iucn_lc = APITestFixtures.create_iucn_status(category='LC')
        iucn_nt = APITestFixtures.create_iucn_status(category='NT')
        iucn_vu = APITestFixtures.create_iucn_status(category='VU')

        # Create endemism
        endemic = APITestFixtures.create_endemism(name='Endemic')

        # Create taxa
        for i in range(5):
            taxon = APITestFixtures.create_taxonomy(
                scientific_name=f'Species {i}',
                canonical_name=f'Species {i}',
                iucn_status=iucn_lc if i < 3 else iucn_nt,
                endemism=endemic if i % 2 == 0 else None,
            )
            self.taxa.append(taxon)

        # Create sites
        coordinates = [
            (-28.5, 24.5),  # Northern Cape
            (-33.9, 18.4),  # Western Cape
            (-26.2, 28.0),  # Gauteng
            (-29.8, 31.0),  # KwaZulu-Natal
            (-25.7, 28.2),  # Mpumalanga
        ]

        for i, (lat, lon) in enumerate(coordinates):
            site = APITestFixtures.create_location_site(
                name=f'Test Site {i + 1}',
                site_code=f'SITE{i + 1:03d}',
                latitude=lat,
                longitude=lon,
                geometry_point=Point(lon, lat, srid=4326),
                validated=i < 4,  # Last one unvalidated
                owner=self.users['regular'],
            )
            self.sites.append(site)

        # Create surveys and records
        for site in self.sites:
            survey = APITestFixtures.create_survey(
                site=site,
                owner=self.users['regular'],
                validated=site.validated,
            )
            self.surveys.append(survey)

            # Create 2-3 records per site
            for j in range(min(3, len(self.taxa))):
                record = APITestFixtures.create_biological_record(
                    site=site,
                    taxonomy=self.taxa[j],
                    survey=survey,
                    owner=self.users['regular'],
                    validated=site.validated,
                )
                self.records.append(record)

        return self


# Pytest fixtures (for pytest-based tests)
@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(db):
    """Return an authenticated API client."""
    user = APITestFixtures.create_user()
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def staff_client(db):
    """Return a staff-authenticated API client."""
    user = APITestFixtures.create_staff_user()
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def superuser_client(db):
    """Return a superuser-authenticated API client."""
    user = APITestFixtures.create_superuser()
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def test_data(db):
    """Return a complete test dataset."""
    return APITestDataSet().setup()

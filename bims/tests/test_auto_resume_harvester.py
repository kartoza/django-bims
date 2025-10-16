from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from unittest.mock import patch, Mock
from bims.tasks import auto_resume_harvest
from bims.tests.model_factories import HarvestSessionF, UserF
from django.core.cache import cache
from django.contrib.auth import get_user_model
from io import BytesIO

User = get_user_model()

class AutoResumeHarvestTestCase(TestCase):
    def setUp(self):
        # Create a user and harvest sessions
        self.user = UserF.create(username='testuser', password='12345')

        # Create mock log files
        self.log_file_content = b"line1\nline2\nlast line"
        self.log_file_mock = SimpleUploadedFile("harvest_log.txt", self.log_file_content)

        self.session1 = HarvestSessionF.create(
            harvester=self.user,
            module_group=None,
            start_time="2023-01-01T00:00:00Z",
            category='gbif',
            finished=False,
            canceled=False,
            log_file=self.log_file_mock
        )

        self.session2 = HarvestSessionF.create(
            harvester=self.user,
            module_group=None,
            start_time="2023-01-02T00:00:00Z",
            category='gbif',
            finished=False,
            canceled=False,
            log_file=self.log_file_mock
        )

        # Set up cache
        cache.set('harvester_keys', [])
        cache.set(f'harvester_{self.session1.id}_last_log', 'last line')

    @patch('bims.tasks.harvest_collections.get_cache', side_effect=cache.get)
    @patch('bims.tasks.harvest_collections.set_cache', side_effect=cache.set)
    @patch('bims.tasks.harvest_collections.delete_cache', side_effect=cache.delete)
    @patch('bims.tasks.harvest_collections.harvest_collections.delay')
    @patch('bims.tasks.harvest_collections.read_last_line')
    def test_auto_resume_harvest(self, mock_read_last_line, mock_harvest_collections, mock_delete_cache, mock_set_cache, mock_get_cache):
        # Mock read_last_line to return the last line of the log file
        mock_read_last_line.return_value = 'last line'

        # Call the auto_resume_harvest task
        auto_resume_harvest()
        auto_resume_harvest()

        # Assertions to ensure the session was resumed
        mock_harvest_collections.assert_called_with(self.session2.id, True, schema_name='public')

        # Assertions to ensure cache was updated
        new_harvester_keys = cache.get('harvester_keys')
        self.assertIn(self.session2.id, new_harvester_keys)

        # Check cache set calls
        mock_set_cache.assert_any_call(f'harvester_{self.session2.id}_last_log', 'last line')
        mock_set_cache.assert_any_call('harvester_keys', [self.session2.id])

    def tearDown(self):
        # Clean up cache
        cache.clear()

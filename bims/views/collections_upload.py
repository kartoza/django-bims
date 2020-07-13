# coding=utf-8
"""Collections uploader view
"""
from bims.views.data_upload import DataUploadView
from bims.tasks.collections_upload import collections_upload


class CollectionsUploadView(DataUploadView):
    """Taxa upload view."""
    template_name = 'collections_uploader.html'
    upload_task = collections_upload
    category = 'collections'

import json
import hashlib
import os
from django.conf import settings
from bims.models.search_process import SearchProcess


def get_or_create_search_process(search_type, query, process_id=None):
    """
    Get or create search process
    :param search_type: Search process type
    :param query: Search query (optional)
    :param process_id: Generated process id
    :return: search_process model, created status
    """
    created = False
    fields = {}
    search_processes = SearchProcess.objects.filter(
        category=search_type
    )
    if query:
        search_processes = SearchProcess.objects.filter(
            query=query
        )
        fields['query'] = query
        fields['process_id'] = hashlib.md5(query).hexdigest()
    if process_id:
        search_processes = SearchProcess.objects.filter(
            process_id=process_id
        )
        fields['process_id'] = process_id
    if len(search_processes) > 1:
        for search_process in search_processes[1:len(search_processes)]:
            search_process.delete()

    if search_processes.exists():
        search_process = search_processes[0]
    else:
        created = True
        search_process = SearchProcess.objects.create(
            category=search_type,
            **fields
        )

    return search_process, created


def create_search_process_file(data, search_process,
                               file_path=None, finished=None):
    """
    Create a file then save it to search process
    """
    try:
        json.dumps(data)
    except ValueError:
        # Not valid json
        return None

    if file_path:
        path_file = file_path
    elif search_process.file_path:
        path_file = search_process.file_path
    else:
        # Generate path file
        if search_process.process_id:
            path_file = search_process.process_id
        elif search_process.query:
            path_file = hashlib.md5(search_process.query).hexdigest()
        else:
            path_file = hashlib.md5(
                json.dumps(data, sort_keys=True)
            ).hexdigest()

    folder = 'search_cluster'
    path_folder = os.path.join(settings.MEDIA_ROOT, folder)
    path_file = os.path.join(path_folder, path_file)
    with open(path_file, 'wb') as status_file:
        status_file.write(json.dumps(data))
        search_process.file_path = path_file
        search_process.save()

    if finished:
        search_process.finished = finished
        search_process.save()

    return search_process.file_path

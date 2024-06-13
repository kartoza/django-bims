from bims.api_views.search import CollectionSearch


def generate_checklist(filters):
    search = CollectionSearch(filters)
    collection_results = search.process_search()

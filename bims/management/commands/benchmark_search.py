import json
import time

from django.core.exceptions import EmptyResultSet
from django.core.management.base import BaseCommand
from django.db import connection
from django.test.utils import CaptureQueriesContext

from bims.api_views.search import CollectionSearch


def bbox(x1, y1, x2, y2):
    return json.dumps([[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]])


FILTERS = {
    'conservation_status': {'conservationStatus': '["CR","EN","VU"]'},
    'text_river': {'search': 'river'},
    'text_no_match': {'search': 'Cyprinidae'},
    'text_taxon': {'search': 'Labeo'},
    'text_site_code': {'search': 'LIM'},
    'polygon_small': {'polygon': bbox(27.9, -26.3, 28.3, -25.9)},
    'polygon_country': {'polygon': bbox(16, -35, 33, -22)},
    'module': {'modules': '1'},
    'year_range': {'yearFrom': '2015', 'yearTo': '2018'},
    'source_collection': {'sourceCollection': '["fbis"]'},
}


class Command(BaseCommand):
    """Benchmark CollectionSearch.process_search() on a tenant.

    Runs each filter shape several times and records the time, number of
    queries and result count, and with --explain the EXPLAIN (ANALYZE,
    BUFFERS) of the records query. The first run is the coldest, the
    best of the following runs is the warm time. Results are written to
    --output as JSON so runs can be compared.

        python manage.py tenant_command benchmark_search --schema=fbis \\
            --output=/tmp/before.json --explain
    """

    help = 'Benchmark CollectionSearch.process_search() filter shapes'

    def add_arguments(self, parser):
        parser.add_argument('--output', default=None)
        parser.add_argument('--runs', type=int, default=3)
        parser.add_argument('--explain', action='store_true', default=False)
        parser.add_argument('--only', default=None,
                            help='Comma separated filter names')

    def handle(self, *args, **options):
        names = (
            options['only'].split(',') if options['only'] else list(FILTERS)
        )
        results = {}
        for name in names:
            params = FILTERS[name]
            timings, queries, count = [], 0, None
            for _ in range(options['runs']):
                with CaptureQueriesContext(connection) as ctx:
                    start = time.time()
                    search = CollectionSearch(params)
                    records = search.process_search()
                    count = records.values('id')[:100001].count()
                    timings.append(round(time.time() - start, 3))
                queries = len(ctx)
            entry = {
                'count': count,
                'first_s': timings[0],
                'warm_s': min(timings[1:] or timings),
                'queries': queries,
            }
            if options['explain']:
                try:
                    sql, sql_params = records.values('id')[:100001].query \
                        .sql_with_params()
                except EmptyResultSet:
                    sql = None
                if sql:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            'EXPLAIN (ANALYZE, BUFFERS) ' + sql, sql_params)
                        entry['explain'] = [
                            row[0] for row in cursor.fetchall()]
            results[name] = entry
            self.stdout.write('{:<22} {:>8} rows  first {:>6}s  warm {:>6}s  '
                              '{} queries'.format(
                                  name, count, entry['first_s'],
                                  entry['warm_s'], queries))
        if options['output']:
            with open(options['output'], 'w') as f:
                json.dump(results, f, indent=2)

# coding: utf-8
from __future__ import print_function

__author__ = 'Alison Mukoma <alison@kartoza.com>'
__copyright__ = 'kartoza.com'
__date__ = '29/06/2018'

from prometheus_client.process_collector import (
    ProcessCollector,
    PROCESS_COLLECTOR)

from prometheus_client import (
    Gauge,
    Counter,
    REGISTRY,
    Histogram,
    generate_latest)


landing_page_counter = Counter(
        'user_opens_landing_page', 'User visits the landing page')


class PrometheusCounter:
    """Count user visits to the site."""

    @staticmethod
    def increase_landing_page_view():
        landing_page_counter.inc()


ProcessCollector(
        namespace='mydaemonCustomCollector',
        pid=lambda: open('/proc/cpuinfo').read())

# Count the total number of HTTP requests that feti is recieving.
REQUESTS = Counter(
        'http_requests_total', 'Total HTTP Requests (count)',
        ['method', 'endpoint', 'status_code'])

# A gauge to monitor the total number of in progress requests
IN_PROGRESS = Gauge(
        'http_requests_inprogress', 'Number of in progress HTTP requests')

# A histogram to measure the latency of the HTTP requests
TIME_DELAY = Histogram(
        'http_request_duration_seconds', 'HTTP request latency (seconds)')


@IN_PROGRESS.track_inprogress()
@TIME_DELAY.time()
def count_200():
    REQUESTS.labels(method='GET', status_code=200).inc()
    return generate_latest(REGISTRY)


@IN_PROGRESS.track_inprogress()
@TIME_DELAY.time()
def count_404():
    REQUESTS.labels(method='GET', status_code=404).inc()
    return generate_latest(REGISTRY)


@IN_PROGRESS.track_inprogress()
@TIME_DELAY.time()
def count_500():
    REQUESTS.labels(method='GET', status_code=500).inc()
    return generate_latest(REGISTRY)


PROCESS_COLLECTION = Gauge(
        'collect_running_process', 'Collect running processes')


@PROCESS_COLLECTION.track_inprogress()
def running_processes():
    PROCESS_COLLECTOR.collect()
    return generate_latest(REGISTRY)

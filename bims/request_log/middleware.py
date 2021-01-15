import socket
import time
from bims.models.request_log import RequestLog


class RequestLogMiddleware(object):
    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):

        # save log_data in some way
        if not request.user.is_anonymous:
            RequestLog.objects.create(
                user=request.user,
                remote_address=request.META['REMOTE_ADDR'],
                server_hostname=socket.gethostname(),
                request_path=request.get_full_path(),
                response_status=response.status_code,
                start_time=request.start_time,
                run_time=time.time() - request.start_time,
            )

        return response

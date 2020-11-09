import socket
import time


class RequestLogMiddleware(object):
    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):

        log_data = {
            'user': request.user.pk,
            'remote_address': request.META['REMOTE_ADDR'],
            'server_hostname': socket.gethostname(),
            'request_method': request.method,
            'request_path': request.get_full_path(),
            'request_body': request.body,
            'response_status': response.status_code,
            'start_time': request.start_time,
            'run_time': time.time() - request.start_time,
        }

        # save log_data in some way
        print(log_data)

        return response

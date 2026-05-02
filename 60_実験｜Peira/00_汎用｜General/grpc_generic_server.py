import grpc
from concurrent import futures
import time

class LoggingInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        print(f"[{time.strftime('%X')}] Intercepted Call:", handler_call_details.method)
        print(f"Invocation Metadata:", handler_call_details.invocation_metadata)
        return continuation(handler_call_details)

class GenericHandler(grpc.GenericRpcHandler):
    def service(self, handler_call_details):
        print(f"[{time.strftime('%X')}] GenericHandler Call:", handler_call_details.method)
        
        def dummy_method(request, context):
            print(f"Received request type: {type(request)}")
            print(f"Received request payload: {request}")
            return b'hello'

        # return grpc.unary_unary_rpc_method_handler(dummy_method)
        return grpc.RpcMethodHandler(
            request_streaming=False,
            response_streaming=False,
            request_deserializer=lambda x: x,
            response_serializer=lambda x: x,
            unary_unary=dummy_method,
        )

def serve(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10),
                         interceptors=(LoggingInterceptor(),))
    server.add_generic_rpc_handlers((GenericHandler(),))
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"gRPC Generic Server listening on port {port}...")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 36989
    serve(port)

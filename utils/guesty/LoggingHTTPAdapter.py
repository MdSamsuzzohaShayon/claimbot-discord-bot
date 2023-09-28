import logging
import httpx

# Create a logger instance
logger = logging.getLogger(__name__)


# Define a custom HTTP adapter to log requests and responses
class LoggingHTTPAdapter(httpx.AsyncHTTPTransport):
    async def handle_request(
            self, request: httpx.Request, **kwargs
    ) -> httpx.Response:
        # Log the request details
        logger.debug(f'Request[s] {request.method} {request.url}')
        logger.debug(f'Headers[s] {request.headers}')
        logger.debug(f'Body[s] {request.content}')

        # Send the request using the parent class's handle_request method
        response = await super().handle_request(request, **kwargs)

        # Log the response details
        logger.debug(f'Response[s] {response.status_code} {response.url}')
        logger.debug(f'Headers[s] {response.headers}')
        logger.debug(f'Body[s] {response.text}')

        return response

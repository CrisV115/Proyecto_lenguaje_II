from django.utils.cache import add_never_cache_headers


class DisableHtmlPageCachingMiddleware:
    """Avoid stale HTML forms reusing outdated CSRF tokens."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        content_type = response.get("Content-Type", "")
        if request.method == "GET" and content_type.startswith("text/html"):
            add_never_cache_headers(response)
        return response

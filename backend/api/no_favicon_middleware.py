# my_app/no_favicon_middleware.py

class NoFaviconMiddleware:
    """
    Middleware that injects a minimal transparent favicon link into HTML responses.
    This prevents the browser from making a separate request to /favicon.ico
    and causing a 404/500 error.
    """
    # A 1x1 pixel transparent GIF as a data URL
    transparent_gif = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Only attempt to modify HTML responses that don't already have a favicon
        if (response.get('Content-Type', '').startswith('text/html') and
                b'rel="icon"' not in response.content):
            content = response.content.decode(response.charset)
            # Insert the link tag right before the closing </head>
            head_end = content.find('</head>')
            if head_end != -1:
                new_content = (content[:head_end] +
                              f'<link rel="icon" href="{self.transparent_gif}" />' +
                              content[head_end:])
                response.content = new_content.encode(response.charset)
                # Update the Content-Length header if it exists
                if 'Content-Length' in response:
                    response['Content-Length'] = str(len(response.content))
        return response
class AdminShortcutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        user = getattr(request, 'user', None)
        content_type = response.get('Content-Type', '')

        if 'text/html' in content_type and hasattr(response, 'content'):
            html = response.content.decode(response.charset or 'utf-8')
            html = html.replace(
                "{% static 'css/style.css' %}",
                "{% static 'css/style.css' %}?v=navy-10"
            )
            html = html.replace(
                '/static/css/style.css"',
                '/static/css/style.css?v=navy-10"'
            )
            html = html.replace(
                '/static/js/theme.js"',
                '/static/js/theme.js?v=navy-10"'
            )
            html = html.replace(
                '/static/js/service-worker.js"',
                '/static/js/service-worker.js?v=navy-10"'
            )
            response.content = html.encode(response.charset or 'utf-8')
            response['Content-Length'] = str(len(response.content))
            response['Cache-Control'] = 'no-store, max-age=0'

        if (
            user
            and user.is_authenticated
            and user.is_superuser
            and 'text/html' in content_type
            and not request.path.startswith('/admin/')
            and hasattr(response, 'content')
        ):
            html = response.content.decode(response.charset or 'utf-8')

            if '</body>' in html and 'class="admin-fab"' not in html:
                button = (
                    '<a href="/admin/" class="admin-fab" '
                    'style="position:fixed;right:22px;bottom:86px;z-index:2147483647;'
                    'display:inline-flex;align-items:center;justify-content:center;gap:8px;'
                    'min-height:46px;padding:0 18px;border-radius:999px;'
                    'border:1px solid rgba(125,211,252,.55);'
                    'background:linear-gradient(135deg,#7dd3fc,#a7f3d0);'
                    'color:#07111f;text-decoration:none;font-weight:800;'
                    'box-shadow:0 18px 38px rgba(0,0,0,.42);'
                    'font-family:Inter,Segoe UI,Arial,sans-serif;">'
                    '&#1040;&#1076;&#1084;&#1110;&#1085;&#1082;&#1072;</a>'
                )
                html = html.replace('</body>', f'{button}</body>', 1)
                response.content = html.encode(response.charset or 'utf-8')
                response['Content-Length'] = str(len(response.content))

        return response

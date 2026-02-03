from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect


class ApiJwtRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith('/api/'):
            if path.startswith('/api/token/'):
                return self.get_response(request)
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if not auth_header.startswith('Bearer '):
                return JsonResponse({'detail': 'Authentication credentials were not provided.'}, status=401)
        return self.get_response(request)


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if self._is_public_path(path):
            return self.get_response(request)
        if request.user.is_authenticated:
            return self.get_response(request)
        return redirect(settings.LOGIN_URL)

    @staticmethod
    def _is_public_path(path: str) -> bool:
        public_prefixes = (
            '/login/',
            '/auth/login/',
            '/auth/logout/',
            '/api/',
            '/admin/',
            '/static/',
            '/media/',
            '/403/',
            '/404/',
            '/500/',
            '/501/',
            '/503/',
            '/errors/',
        )
        return path.startswith(public_prefixes)

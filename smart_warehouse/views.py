import json

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST


@ensure_csrf_cookie
def index(request):
    return render(request, 'home.html')


@ensure_csrf_cookie
def equipment_page(request):
    return render(request, 'equipment.html')


@ensure_csrf_cookie
def issue_page(request):
    return render(request, 'issue.html')


@ensure_csrf_cookie
def return_page(request):
    return render(request, 'return.html')


@ensure_csrf_cookie
def inventory_page(request):
    return render(request, 'inventory.html')


@ensure_csrf_cookie
def reports_page(request):
    return render(request, 'reports.html')


@ensure_csrf_cookie
def notifications_page(request):
    return render(request, 'notifications.html')


@ensure_csrf_cookie
def login_page(request):
    return render(request, 'login.html')


@ensure_csrf_cookie
def profile_page(request):
    return render(request, 'profile.html')


@require_POST
def session_login(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        data = request.POST
    username = data.get('username')
    password = data.get('password')
    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({'detail': 'Invalid credentials'}, status=401)
    login(request, user)
    return JsonResponse({'status': 'ok'})


@require_POST
def session_logout(request):
    logout(request)
    return JsonResponse({'status': 'ok'})


def error_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)


def error_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)


def error_500(request):
    return render(request, 'errors/500.html', status=500)


def error_501(request):
    return render(request, 'errors/501.html', status=501)


def error_503(request):
    return render(request, 'errors/503.html', status=503)

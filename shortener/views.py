from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.contrib import messages
from .models import ShortenedURL, URLAccess
import json
import hashlib
from datetime import timedelta
from urllib.parse import urlparse

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

def generate_short_code(url):
    # Generate short code from original URL
    hash_input = url.encode('utf-8')
    hash_object = hashlib.sha256(hash_input)
    return hash_object.hexdigest()[:7]

def home(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        try:
            hours = int(request.POST.get('expiry_hours', 24))
        except ValueError:
            hours = 24
        password = request.POST.get('password')

        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            messages.error(request, 'Invalid URL format')
            return render(request, 'shortener/home.html')

        # Generate short code
        short_code = generate_short_code(url)

        # Check if URL already exists
        existing_url = ShortenedURL.objects.filter(original_url=url).first()
        if existing_url:
            if existing_url.is_expired():
                existing_url.delete()
            else:
                shortened_url = request.build_absolute_uri(f'/{existing_url.short_code}/')
                return render(request, 'shortener/home.html', {
                    'shortened_url': shortened_url,
                    'short_code': existing_url.short_code,
                    'expires_at': existing_url.expires_at,
                    'password': existing_url.password,
                    'is_already_shortened': True
                })
        

        # Create new shortened URL
        shortened = ShortenedURL(
            original_url=url,
            short_code=short_code,
            expires_at=timezone.now() + timedelta(hours=hours),
            password=password
        )
        shortened.save()

        shortened_url = request.build_absolute_uri(f'/{shortened.short_code}/')
        return render(request, 'shortener/home.html', {
            'shortened_url': shortened_url,
            'short_code': shortened.short_code,
            'expires_at': shortened.expires_at,
            'password': shortened.password,
            'is_already_shortened': False
        })

    return render(request, 'shortener/home.html')

def redirect_to_original(request, short_code):
    try:
        url = get_object_or_404(ShortenedURL, short_code=short_code)
        
        if url.is_expired():
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({'error': 'URL has expired'}, status=410)
            messages.error(request, 'This URL has expired')
            return redirect('home')
        
        if url.password:
            provided_password = request.GET.get('password')
            if not provided_password or provided_password != url.password:
                if request.headers.get('Accept') == 'application/json':
                    return HttpResponseForbidden('Password required or incorrect')
                return render(request, 'shortener/password_required.html', {'short_code': short_code})

        # Log access
        URLAccess.objects.create(
            url=url,
            ip_address=get_client_ip(request)
        )
        
        # Update access count
        url.access_count += 1
        url.save()

        return redirect(url.original_url)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('home')

def analytics_lookup(request):
    short_code = request.GET.get('short_code')
    if not short_code:
        return render(request, 'shortener/analytics.html')

    try:
        url = get_object_or_404(ShortenedURL, short_code=short_code)
        
        if url.password:
            provided_password = request.GET.get('password')
            if not provided_password or provided_password != url.password:
                messages.error(request, 'Invalid password')
                return render(request, 'shortener/analytics.html')

        accesses = url.accesses.all().order_by('-accessed_at')
        analytics_data = {
            'original_url': url.original_url,
            'short_code': url.short_code,
            'created_at': url.created_at,
            'expires_at': url.expires_at,
            'is_expired': url.is_expired(),
            'total_accesses': url.access_count,
            'recent_accesses': [
                {
                    'timestamp': access.accessed_at,
                    'ip_address': access.ip_address
                }
                for access in accesses[:10]
            ]
        }
        
        return render(request, 'shortener/analytics.html', {'analytics': analytics_data})
    except Exception as e:
        messages.error(request, str(e))
        return render(request, 'shortener/analytics.html')

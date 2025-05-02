from django.shortcuts import redirect
from django.urls import reverse
from django.http import JsonResponse


class BanActionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.method == 'POST':
            is_ban = False

            # Check if user is banned via ReaderProfile
            if hasattr(request.user, 'readerprofile') and request.user.readerprofile.is_ban:
                is_ban = True
                print(f"User {request.user.username} is banned (ReaderProfile).")

            # Check if user is banned via Author
            elif hasattr(request.user, 'author') and request.user.author.is_ban:
                is_ban = True
                print(f"User {request.user.username} is banned (Author).")

            # If user is banned, block POST actions
            if is_ban:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    # For AJAX requests (e.g., Like button, Comment submit)
                    return JsonResponse({'error': 'You are banned from performing this action.'}, status=403)
                else:
                    # For regular POST requests, redirect to banned info page
                    return redirect('banned_action_page')

        # Continue with the request if not banned or not a POST request
        response = self.get_response(request)
        return response
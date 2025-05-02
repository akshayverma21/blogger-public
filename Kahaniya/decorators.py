from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from .models import Author, ReaderProfile




def author_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user

        # Check if user is authenticated
        if not user.is_authenticated:
            messages.error(request, "You must be logged in.")
            return redirect('account_login')

        # Check ReaderProfile and ban status
        try:
            reader_profile = ReaderProfile.objects.get(user=user)
            if reader_profile.is_ban:
                messages.error(request, "You are banned from performing this action.")
                return redirect('blog_home')
        except ReaderProfile.DoesNotExist:
            messages.error(request, "Reader profile is required.")
            return redirect('blog_home')

        # Check Author status
        try:
            author = Author.objects.get(user=user)
            if not author.is_approved:
                if author.has_applied_for_author:
                    messages.error(request, "Your author application is pending.")
                else:
                    messages.error(request, "You must be an approved author.")
                return redirect('blog_home')
        except Author.DoesNotExist:
            messages.error(request, "You must apply to become an author.")
            return redirect('create_author')

        # User is an approved author, proceed to view
        return view_func(request, *args, **kwargs)
    return wrapper




def check_ban(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user=request.user

        if not user.is_authenticated:
            messages.error(request, 'plz login first')
            return redirect('account_login')
        try:
            reader_profile=ReaderProfile.objects.get(user=request.user)
            if reader_profile.is_ban:
                messages.error(request,"you are banned from performing this action.")
                return redirect("blog_home")
        except ReaderProfile.DoesNotExist:
            messages.error(request, "proifile not found, plz login")
            return redirect("account_login")
        

        return view_func(request,*args, **kwargs)
    return wrapper

from Kahaniya.models import BookMark,Blogpost  # Adjust import based on your app structure

def user_bookmarks(request):
    if request.user.is_authenticated:
        save_posts = BookMark.objects.filter(user=request.user).select_related('content_type', 'user')
    else:
        save_posts = []
    return {'save_posts': save_posts}


def category_context(request):
    category_choices = dict(Blogpost.category)
    slug_to_code = {
        'adult': 'A',
        'fiction': 'F',
        'fantasy': 'FT',
        'love-story': 'Lv',
    }
    selected_category = None
    for slug, code in slug_to_code.items():
        if f'/category/{slug}/' in request.path:
            selected_category = code
            break
    return {
        'categories': category_choices,
        'selected_category': selected_category,
    }
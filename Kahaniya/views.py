from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from .models import Author, Blogpost, User, ReaderProfile, Comment, PostLikes, BookMark, Follow
from django.core.paginator import Paginator
from .forms import Authorform, Blogform, ReaderProfileForm, Commentform
from django.contrib import messages
from django.http import HttpResponseForbidden, Http404
from django.contrib.auth.hashers import make_password
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Case, When, Value, DateTimeField
from django.contrib.auth import logout
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import F
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth.decorators import login_required
from .decorators import author_required, check_ban
# Create your views here.


#BLOGHOMEPAGE
def Blog_home(request,category=None):
    # Get sorting parameter
    sort_by = request.GET.get('sort', 'newest')

    # Base queryset with prefetch for efficiency
    posts = Blogpost.objects.all().prefetch_related('likes', 'comments', 'bookmark', 'author')
    
    category_choices = dict(Blogpost.category)  # e.g., {'A': 'ADULT', 'F': 'fiction', ...}

    # Filter posts by category if provided
    if category:
        # Validate category
        if category not in category_choices:
            # Handle invalid category (e.g., redirect or show all posts)
            posts = Blogpost.objects.all().order_by('-created_at')
            selected_category = None
        else:
            posts = Blogpost.objects.filter(category_choices=category).order_by('-created_at')
            selected_category = category
    else:
        posts = Blogpost.objects.all().order_by('-created_at')
        selected_category = None


    # Apply sorting
    if sort_by == 'newest':
        posts = posts.order_by('-created_at')
    elif sort_by == 'latest_comment':
        posts = posts.annotate(
            latest_comment=Max('comments__created_at')
        ).annotate(
            sort_time=Case(
                When(latest_comment__isnull=False, then='latest_comment'),
                default='created_at',
                output_field=DateTimeField()
            )
        ).order_by('-sort_time')
    elif sort_by == 'most_likes':
        posts = posts.annotate(
            like_count=Count('likes')
        ).order_by('-like_count', '-created_at')
    elif sort_by == 'most_comments':
        posts = posts.annotate(
            comment_count=Count('comments')
        ).order_by('-comment_count', '-created_at')
    

    # Pagination
    paginator = Paginator(posts, 5)  # 5 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    for blog in page_obj:
        blog.user_liked = PostLikes.objects.filter(
        content_type=ContentType.objects.get_for_model(Blogpost),
        object_id=blog.id,
        user=request.user
        ).exists() if request.user.is_authenticated else False

    recent_posts = Blogpost.objects.all().select_related('author').order_by('-created_at')[:5]
    save_posts = []
    if request.user.is_authenticated:
        save_posts = BookMark.objects.filter(user=request.user, content_type=ContentType.objects.get_for_model(Blogpost))

    context = {
        'page_obj': page_obj,
        'sort_by': sort_by,
        'recent_posts':recent_posts,
        'save_posts':save_posts,
        'category_choices': Blogpost.category,
        'categories': category_choices,
        'selected_category': selected_category,
    }
    return render(request, 'blog_home.html', context)


def process_comment_likes(comment, user):
    comment_ct = ContentType.objects.get_for_model(Comment)
    comment.liked_count_value = PostLikes.objects.filter(content_type=comment_ct, object_id=comment.id).count()
    comment.user_liked = user.is_authenticated and PostLikes.objects.filter(
        content_type=comment_ct,
        object_id=comment.id,
        user=user
    ).exists()

    # Recursively process replies of this comment
    for reply in comment.replies.all():
        process_comment_likes(reply, user)

def Blog_detail(request, blog_id):
    sort_by = request.GET.get('sort', 'newest')
    blog_post = get_object_or_404(Blogpost, id=blog_id)
    comments = Comment.objects.filter(object_id=blog_post.id, parent__isnull=True).select_related('user').prefetch_related('replies')

    # Check if edit mode is triggered
    edit_comment_id = request.GET.get("edit")
    edit_form = None

    recent_posts = Blogpost.objects.all().order_by('-created_at')[:5]

    if request.method == "POST" and request.POST.get("comment_id"):
        # Edit comment
        comment_id = request.POST.get("comment_id")
        comment_to_edit = get_object_or_404(Comment, id=comment_id)

        if comment_to_edit.user == request.user or request.user.is_staff:
            form = Commentform(request.POST, instance=comment_to_edit)
            if form.is_valid():
                form.save()
                messages.success(request, "Your comment has been updated.")
                return redirect('blog_detail', blog_id=blog_id)
            else:
                edit_form = form  # Show form with errors
                edit_comment_id = comment_id  # Stay in edit mode
        else:
            messages.error(request, "You are not authorized to edit this comment.")
            return redirect('blog_detail', blog_id=blog_id)
    else:
        form = Commentform()

    # Prepare edit form if edit mode is triggered
    if edit_comment_id and request.method != "POST":
        comment_to_edit = get_object_or_404(Comment, id=edit_comment_id)
        if comment_to_edit.user == request.user or request.user.is_staff:
            edit_form = Commentform(instance=comment_to_edit)
  
    # Likes and bookmarks
    save_posts = []
    if request.user.is_authenticated:
        save_posts = BookMark.objects.filter(user=request.user, content_type=ContentType.objects.get_for_model(Blogpost))

    user_liked = False
    user_bookmarked = False
    if request.user.is_authenticated:
        user_liked = blog_post.likes.filter(user=request.user).exists()
        user_bookmarked = blog_post.bookmark.filter(user=request.user).exists()

    # Comment likes
    for comment in comments:
        process_comment_likes(comment, request.user)
    
    


    return render(request, 'blog_detail.html', {
        'blog_post': blog_post,
        'form': form,
        'comments': comments,
        'user_bookmarked': user_bookmarked,
        'user_liked': user_liked,
        'save_posts': save_posts,
        'edit_comment_id': edit_comment_id,
        'edit_form': edit_form,
        'recent_posts':recent_posts
    })





#BLOGCREATELOGIC



@author_required
@login_required
def Create_blog(request):
    if request.method=='POST':      
        form= Blogform(request.POST, request.FILES) 
        if form.is_valid(): 
            blog= form.save(commit=False) 
            blog.user=request.user
            try:
                blog.author = Author.objects.get(user=request.user)  
            except Author.DoesNotExist:
                messages.error(request, "You need an Author profile to create a blog post.")
                return redirect('blog_home')                           
            blog.save()                                                           
            messages.success(request,'your post has been sumbitted') 
            return redirect('blog_home') 
    else:                                  
        form=Blogform()  
        
    return render(request, 'blog/blog_create.html', {'form':form} )



@author_required
@login_required
def Edit_blog(request, blog_id):
    blog_post = get_object_or_404(Blogpost, id=blog_id)
    if request.method == 'POST':
        form = Blogform(request.POST, request.FILES, instance=blog_post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your edit has been saved.')
            return redirect('blog_home')
        else:
            messages.error(request, 'Form is not valid!')
    else:
        form = Blogform(instance=blog_post)

    return render(request, 'blog/blog_edit.html', {'form': form})


@author_required
@login_required
def Delete_blog(request, blog_id):
    blog_post = get_object_or_404(Blogpost, id=blog_id)


    if request.method == 'POST':
        blog_post.delete()
        messages.success(request, 'Your post has been deleted.')
        return redirect('blog_home')

    return render(request, 'blog/blog_delete.html', {'blog_post': blog_post})
    
            
    
#AUTHOR LOGIC
@check_ban
@login_required
def create_author(request):
    # Check if user already has an Author object
    existing_author = Author.objects.filter(user=request.user).first()
    
    if existing_author:
        if existing_author.is_approved:
            messages.error(request, "You are already an approved author.")
        else:
            messages.error(request, "You have already applied to be an author. Please wait for approval.")
        return redirect('blog_home')
         
    if request.method == 'POST':
        form = Authorform(request.POST, request.FILES)
        if form.is_valid():
            author = form.save(commit=False)
            author.user = request.user
            author.email = request.user.email 
            author.has_applied_for_author = True
            author.is_approved = False
            author.save()
            messages.success(request, 'Your request to become an author has been submitted. Please wait for approval.')
            return redirect('blog_home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = Authorform()
    
    return render(request, 'author/create_author.html', {'form': form})


@login_required
def author_profile(request,author_id):
    author_profile=get_object_or_404(Author, id=author_id)
    if not (request.user.is_staff or (author_profile.user == request.user and author_profile.is_approved)):
        messages.error(request, "You are not authorized to view this profile.")
        return redirect('blog_home')
    posts=Blogpost.objects.filter(author=author_profile).order_by('-created_at')
    comments = Comment.objects.filter(user=author_profile.user).order_by('-created_at')
    bookmark = BookMark.objects.filter(user=author_profile.user).order_by('-timestamp')
    return render(request, 'author/author_profile.html',
    {'author_profile': author_profile, 'posts':posts, 'comments':comments, 'bookmark':bookmark})

@check_ban
@login_required
def author_edit(request, author_id):
    author_profile=get_object_or_404(Author, id=author_id)
    if not (request.user.is_staff or (author_profile.user == request.user and author_profile.is_approved)):
        messages.error(request, "You are not authorized to edit this profile.")
        return redirect('blog_home')
    if request.method=='POST':
        form=Authorform(request.POST,request.FILES,instance=author_profile)
        if form.is_valid():
            profile=form.save(commit=False)
            profile.save()
            messages.success(request, 'your profile has been updated')
            return redirect('author_profile',author_id=author_id)
        else:
            messages.error(request,'try again later')
    else:
        form=Authorform(instance=author_profile)

    return render(request, 'author/author_edit.html', {'form':form, 'author_id':author_id})
            
@login_required
def author_delete(request, author_id):
    author_profile=get_object_or_404(Author, id=author_id)
    if not (request.user.is_staff or author_profile.user == request.user):
        messages.error(request, "You are not authorized to delete this profile.")
        return redirect('blog_home')
    
    if not author_profile.is_approved:
        messages.error(request, "Your author profile is not approved yet.")
        return redirect('blog_home')
    
    if request.method=="POST":
        author_profile.delete()
        messages.success(request, 'your author account has been deleted')
        return redirect('blog_home')
    return render(request, 'author/author_profile.html', {'author_profile': author_profile})

@login_required
def author_setting(request, author_id):
    author_profile=get_object_or_404(Author, id=author_id)

    if not (request.user.is_staff or author_profile.user == request.user):
        messages.error(request, "You are not authorized to edit this profile.")
        return redirect('blog_home')

    # Ensure only approved authors can edit settings
    if not author_profile.is_approved:
        messages.error(request, "Your author profile is not approved yet.")
        return redirect('blog_home')
    

    if request.method == 'POST' and 'delete_account' not in request.POST:
        form = Authorform(request.POST, request.FILES, instance=author_profile, user=request.user)
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if form.is_valid():
            # Update password if provided
            if password:
                if password == confirm_password:
                    if len(password) < 8:
                        messages.error(request, "Password must be at least 8 characters long.")
                        return render(request, 'author/author_setting.html', {
                            'author_profile': author_profile,
                            'form': form
                        })
                    author_profile.user.set_password(password)
                else:
                    messages.error(request, "Passwords do not match.")
                    return render(request, 'author/author_setting.html', {
                        'author_profile': author_profile,
                        'form': form
                    })

            # Save Author and User
            form.save()
            author_profile.user.email = form.cleaned_data['email']
            author_profile.user.save()
            messages.success(request, "Your settings have been updated.")
            return redirect('author_profile', author_id=author_profile.id)
    else:
        form = Authorform(instance=author_profile, user=request.user)

    return render(request, 'author/author_setting.html', {
        'author_profile': author_profile,
        'form': form
    })

#READER NORMAL USER LOGIC
def reader_view(request):
    reader_profile = request.user.readerprofile
    blogpost_content_type = ContentType.objects.get_for_model(Blogpost)
    recent_posts = Blogpost.objects.all().order_by('-created_at')[:5]
    comments = Comment.objects.filter(
        user=request.user,  # Only comments by the logged-in user
        content_type=blogpost_content_type,  # Only Blogpost comments
        object_id__in=Blogpost.objects.values('id')  # Only existing Blogposts
    ).order_by('-created_at').select_related('user', 'content_type')

    bookmark=BookMark.objects.filter(user=request.user).order_by('-timestamp')
    context = {
        'reader_profile': reader_profile,
        'comments': comments,
        'bookmark': bookmark,
        'recent_posts':recent_posts
    }
    return render(request, 'readers/reader_profile.html', context)

@login_required
def reader_setting(request):
    reader_profile=request.user.readerprofile

    if not (request.user.is_staff or request.user == request.user):
        messages.error(request, 'you are not authorise to do that')
        return redirect('blog_home')
    
    if request.method == 'POST' and 'delete_account' not in request.POST:
        form = ReaderProfileForm(request.POST, request.FILES, instance=reader_profile)
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if form.is_valid():
            if password:
                if password==confirm_password:
                    if len(password)<8:
                        messages.error(request,'password must be at least 8 character long')
                        return render(request, 'readers/reader_setting.html',
                        {'reader_profile':reader_profile,'form':form})
                    reader_profile.user.set_password(password)
                else:
                    messages.error(request, "Passwords do not match.")
                    return render(request, 'readers/reader_setting.html', {
                        'reader_profile': reader_profile,
                        'form': form
                    })
            form.save()
            reader_profile.user.email=form.cleaned_data['email']
            reader_profile.user.save()
            messages.success(request, "Your settings have been updated.")
            return redirect('reader_profile')
    else:
        form = ReaderProfileForm(instance=reader_profile)

    return render(request, 'readers/reader_setting.html', {
        'reader_profile': reader_profile,
        'form': form
    })
       
                    
@check_ban
@login_required
def reader_edit(request):
    reader_profile = request.user.readerprofile
    if request.method == 'POST':
        form=ReaderProfileForm(request.POST, request.FILES, instance=reader_profile)
        if form.is_valid():
            reader=form.save(commit=False)
            reader.save()
            messages.success(request, 'your profile updated')
            return redirect('blog_home')
        else:
            messages.error(request, 'try again')
    else:
        form=ReaderProfileForm(instance=reader_profile)

    return render(request, 'readers/reader_edit.html',{'form':form})


@login_required
def reader_delete(request):
    user = request.user
    if request.method == 'POST':
        logout(request)  # Log out before deleting the user
        user.delete()    # This deletes the user and cascades to ReaderProfile
        messages.success(request, 'Your account has been deleted.')
        return redirect('blog_home')

    return render(request, 'readers/reader_delete.html', {'reader_profile': getattr(user, 'readerprofile', None)})



#FORVIEWER TO SEE AUTHOR AND READER
def public_reader_profile(request, username):
    user = get_object_or_404(User, username=username)
    recent_posts = Blogpost.objects.all().order_by('-created_at')[:5]

    if request.user.is_authenticated and request.user == user:
        return redirect('reader_profile')
    reader_profile = get_object_or_404(ReaderProfile, user=user)

    blogpost_content_type = ContentType.objects.get_for_model(Blogpost)
    comments = Comment.objects.filter(
        user=user,
        content_type=blogpost_content_type,
        object_id__in=Blogpost.objects.values('id')
    ).order_by('-created_at').select_related('user', 'content_type')

    bookmark = BookMark.objects.filter(user=user).order_by('-timestamp')

    context = {
        'reader_profile': reader_profile,
        'comments': comments,
        'bookmark': bookmark,
        'recent_posts':recent_posts
        
    }
    return render(request, 'readers/public_reader_profile.html', context)



def public_author_profile(request,username):
    user=get_object_or_404(User,username=username)
    author_profile = get_object_or_404(Author, user=user)
    recent_posts = Blogpost.objects.all().order_by('-created_at')[:5]

    if request.user.is_authenticated and request.user == user:
        return redirect('author_profile',author_id=author_profile.id) 
    try:
        author_profile = Author.objects.get(user=user)
    except Author.DoesNotExist:
        return render(request, '404.html', {'message': 'Author profile not found'}, status=404)

    posts = Blogpost.objects.filter(author=author_profile).order_by('-created_at')

    is_following = False
    if request.user.is_authenticated and request.user != user:
       is_following = Follow.objects.filter(user=request.user, author=author_profile).exists()

    content_type=ContentType.objects.get_for_model(Blogpost)
    comments=Comment.objects.filter(
        user=user,
        content_type=content_type,
        object_id__in=Blogpost.objects.values_list("id", flat=True)
    ).order_by('-created_at').select_related('user', 'content_type')

    bookmark=BookMark.objects.filter(user=user).order_by('-timestamp')

    context={
        'author_profile':author_profile,
        'comments':comments,
        'bookmark':bookmark,
        'posts':posts,
        'is_following':is_following,
        'recent_posts':recent_posts
    }
    return render (request, 'author/public_author_profile.html',context)
    


def user_profile_redirect(request, username):
    user=get_object_or_404(User, username=username)

    try:
        return redirect('reader_profile',pk=user.readerprofile.pk)
    except ReaderProfile.DoesNotExist:
        pass

    try:
        return redirect('author_profile', pk=user.authorprofile.pk)
    except Author.DoesNotExist:
        pass

    return redirect('blog_home')

@check_ban
@login_required
def edit_comment(request, comment_id):
    comment=get_object_or_404(Comment,id=comment_id)

    if comment.user!=request.user and not request.user.is_staff:
        messages.error(request, 'you are not authorize to edit comment')
        return redirect('blog_detail', blog_id=comment.object_id)
    
    if request.method== "POST":
        form=Commentform(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, 'your comment has been edited')
            return redirect('blog_detail', blog_id=comment_id)
    else:
        form=Commentform(instance=comment)

    return render(request, "comments/edit_comment.html", {'form':form, 'comment':comment})
   


#COMMENTS LOGIC
@check_ban
@login_required
def add_comment(request, app_label, model_name, object_id):
    content_type = get_object_or_404(ContentType, app_label=app_label, model=model_name)
    obj = get_object_or_404(Blogpost, id=object_id)  # Directly use Blogpost
    form = Commentform(request.POST or None)

    if request.method == "POST" and form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.content_type = content_type
        comment.object_id = object_id
        parent_id = request.POST.get('parent_id')
        if parent_id:
            parent_comment = Comment.objects.filter(id=parent_id).first()
            comment.parent = parent_comment
        comment.save()
        return redirect('blog_detail', blog_id=object_id)

    comments = Comment.objects.filter(
        object_id=object_id, parent__isnull=True
    ).select_related('user').prefetch_related('replies')

    comment_ct = ContentType.objects.get_for_model(Comment)

    for comment in comments:
        comment.liked_count = PostLikes.objects.filter(
            content_type=comment_ct,
            object_id=comment.id
        ).count()

        comment.user_liked = PostLikes.objects.filter(
            content_type=comment_ct,
            object_id=comment.id,
            user=request.user
        ).exists()

        for reply in comment.replies.all():
            reply.liked_count = PostLikes.objects.filter(
                content_type=comment_ct,
                object_id=reply.id
            ).count()

            reply.user_liked = PostLikes.objects.filter(
                content_type=comment_ct,
                object_id=reply.id,
                user=request.user
            ).exists()


    return render(request, "blog_detail.html", {'blog_post': obj, 'form': form,
        'comments': comments
    })


@check_ban
@login_required
def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    if request.method == "POST":
        if comment.user == request.user:
            # Store content object for redirection
            content_object = comment.content_object
            comment.delete()
            messages.success(request, 'Your comment has been deleted.')
            # Redirect to the blog post or relevant page
            return redirect(reverse('blog_detail', kwargs={'blog_id': content_object.id}))
        else:
            messages.error(request, "You cannot delete someone else's comment.")
            return redirect(request.META.get('HTTP_REFERER', 'home'))  # Fallback to 'home' URL
    return redirect(request.META.get('HTTP_REFERER', 'home'))


#LIKE
@check_ban
@login_required
def toggle_like(request, app_label, model_name, object_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    content_type = get_object_or_404(ContentType, app_label=app_label, model=model_name)
    model_class = content_type.model_class()
    content_object = get_object_or_404(model_class, id=object_id)

    like_obj, created = PostLikes.objects.get_or_create(
        user=request.user,
        content_type=content_type,
        object_id=object_id
    )

    if not created:
        # Already liked, so we remove the like
        like_obj.delete()  # ✅ This must be the model instance
    else:
        like_obj.like = True
        like_obj.save()

    return redirect(request.META.get('HTTP_REFERER', '/'))




#SAVE POST

def book_mark(request, app_label, model_name, object_id):
    if not request.user.is_authenticated:
        return redirect('account_login')

    content_type = get_object_or_404(ContentType, app_label=app_label, model=model_name)
    model_class = content_type.model_class()
    content_object = get_object_or_404(model_class, id=object_id)

    bookmark_obj, created = BookMark.objects.get_or_create(
        user=request.user,
        content_type=content_type,
        object_id=object_id
    )

    if not created:
        bookmark_obj.delete()

    return redirect(request.META.get('HTTP_REFERER', '/'))


#FOLLOW AUTHOR 
@check_ban
@login_required
def follow_author(request,author_id):
    if not request.user.is_authenticated:
        return redirect('account_login')
    
    author=get_object_or_404(Author,id=author_id)

    if Follow.objects.filter(user=request.user, author=author).exists():
        messages.info(request,'you are already following the author')
    else:
        Follow.objects.create(user=request.user,author=author)
        messages.success(request, f"you are following {author.name}")

    return redirect(request.META.get('HTTP_REFERER', '/'))

@check_ban
@login_required
def unfollow_author(request, author_id):
    if not request.user.is_authenticated:
        return redirect('account_login')
    
    author=get_object_or_404(Author,id=author_id)


    follow=Follow.objects.filter(user=request.user, author=author)
    if follow.exists():
        follow.delete()
        messages.success(request, f'you unfollowed {author.name}')
    else:
        messages.info(request, 'you are not following this author')

    return redirect(request.META.get('HTTP_REFERER', '/'))

#FOLLOWERLIST AND FOLLOWING LIST
def follower_list(request, username):
    author=get_object_or_404(Author, user__username=username)
    followers=Follow.objects.filter(author=author)
    follower_users=[follower.user for follower in followers]
    follower_count=followers.count()

    user_following_ids = []
    if request.user.is_authenticated:
        user_following_ids = list(
            Follow.objects.filter(user=request.user).values_list('author__id', flat=True)
        )

    return render(request, 'author/followers_list.html',{'followers': follower_users, 'author': author,
    'follower_count':follower_count, 'user_following_id':user_following_ids})


def following_list(request, username):
    author = get_object_or_404(Author, user__username=username)
    user = author.user  # the user account behind this author

    following = Follow.objects.filter(user=user).select_related('author')
    following_authors = [follow.author for follow in following]
    following_count = following.count()

    user_following_ids = []
    if request.user.is_authenticated:
        user_following_ids = list(
            Follow.objects.filter(user=request.user).values_list('author__id', flat=True)
        )

    return render(request, 'author/following_list.html', {
        'following': following_authors,
        'author': author,
        'following_count': following_count,
        'user_following_id': user_following_ids,
    })
    

def reader_following_list(request, username):
    user = get_object_or_404(User, username=username)
    reader_profile = get_object_or_404(ReaderProfile, user=user)

    # Get all Follow objects where this reader (user) is the follower
    follow_objects = Follow.objects.filter(user=user).select_related('author')
    following_authors = [follow.author for follow in follow_objects]

    # Logged-in user: who they are following
    user_following_ids = []
    if request.user.is_authenticated:
        user_following_ids = list(
            Follow.objects.filter(user=request.user).values_list('author__id', flat=True)
        )
    
    return render(request, 'readers/reader_following_list.html', {
        'reader': reader_profile,
        'following_authors': following_authors,
        'user_following_id': user_following_ids,
        'following_count': len(following_authors)
    })

def searchList(request):
    query = request.GET.get("q", "").strip()
    results = []

    if query:
        # Full-text search for title and content
        search_vector = SearchVector("title", "content")
        search_query = SearchQuery(query, config='english', search_type='plain')  # Plain search to include stop words

        # Combine full-text search with category_choices lookup
        results = Blogpost.objects.annotate(
            rank=SearchRank(search_vector, search_query)
        ).filter(
            Q(rank__gte=0) |  # Include all full-text matches (even low rank)
            Q(category_choices__icontains=query) |  # Match category codes (e.g., 'A')
            Q(category_choices__in=Blogpost.objects.filter(
                category_choices__iexact=query
            ).values('category_choices')) |  # Match category display names
            Q(content__icontains=query) |  # Fallback for content
            Q(title__icontains=query)  # Fallback for title
        ).order_by('-rank', '-created_at').distinct()

    return render(request, "search/search.html", {
        "search": results,
        "query": query,
    })

@check_ban
@login_required
def adminpanel(request):
    if not request.user.is_staff:
        return redirect('blog_home')
    
    # Normal users: Users with ReaderProfile but no Author object
    normal_users = ReaderProfile.objects.filter(is_ban=False).select_related('user')
    
    # Get pending and approved author objects
    pending_authors = Author.objects.filter(has_applied_for_author=True, is_approved=False).select_related('user')
    approved_authors = Author.objects.filter(is_approved=True).select_related('user')

    # All author user IDs (optional if needed in template logic)
    approved_author_ids = set(approved_authors.values_list('user_id', flat=True))

    return render(request, 'admin/adminpanel.html', {
        'normal_users': normal_users,
        'pending_authors': pending_authors,
        'approved_authors': approved_authors,
        'approved_author_ids': approved_author_ids,
    })

@login_required
def review_author_application(request, user_id):
    application = get_object_or_404(Author, user__id=user_id)

    # Check if already approved
    if application.is_approved:
        return redirect('view_author_profile', user_id=user_id)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "approve":
            # ✅ Update the existing Author instead of creating
            application.is_approved = True
            application.save()
        elif action == "reject":
            if hasattr(application.user, 'authorprofile'):
                application.user.authorprofile.delete()
            application.delete()
            messages.success(request, "Author application has been rejected and profiles deleted.")
        return redirect('admin_panel')
        

    return render(request, 'admin/author_application_detail.html', {
        'application': application
    })

    

@login_required
def admin_view_author_profile(request, user_id):
    if not request.user.is_staff:
        return redirect('blog_home')

    user = get_object_or_404(User, id=user_id)
    author = get_object_or_404(Author, user=user)
    reader_profile = get_object_or_404(ReaderProfile, user=user)
    posts = Blogpost.objects.filter(author=author)
    comments = Comment.objects.filter(user=user)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "remove_author":
            author.delete()
            messages.success(request, f"{user.username} is no longer an author.")
            return redirect('admin_panel')
        elif action == "ban":
            reader_profile.is_ban = True
            reader_profile.save()
            messages.success(request, f"{user.username} has been banned.")
            return redirect('admin_panel')

    return render(request, 'admin/author_profile_detail.html', {
        'author': author,
        'posts': posts,
        'comments': comments
    })


@user_passes_test(lambda u: u.is_superuser)
def update_user_status(request, user_id):
    user=get_object_or_404(ReaderProfile,id=user_id)

    if request.method== 'POST':
        user.is_author='is_author'
        user.is_ban='is_ban'
        user.save()


    return redirect('admin_panel')



@login_required
def edit_user_status(request, user_id):
    try:
        user = get_object_or_404(User, id=user_id)
    except User.DoesNotExist:
        messages.error(request, f"No user found with ID {user_id}.")
        return redirect('admin_panel')

    try:
        reader_profile = get_object_or_404(ReaderProfile, user=user)
    except ReaderProfile.DoesNotExist:
        messages.error(request, f"No reader profile found for user {user.username}.")
        return redirect('admin_panel')

    action = request.GET.get('action')

    if action == 'ban':
        reader_profile.is_ban = True
        reader_profile.save()
        messages.success(request, f"{user.username} has been banned.")

    elif action == 'unban':
        reader_profile.is_ban = False
        reader_profile.save()
        messages.success(request, f"{user.username} has been unbanned.")

    elif action == 'make_author':
        try:
            author = Author.objects.get(user=user)
            if author.is_approved:
                messages.info(request, f"{user.username} is already an approved author.")
            else:
                author.is_approved = True
                author.has_applied_for_author = False
                author.save()
                messages.success(request, f"{user.username} is now an approved author.")
        except Author.DoesNotExist:
            messages.error(request, f"{user.username} has not applied to be an author.")


    elif action == 'remove_author':
        try:
           author = Author.objects.get(user=user)
           author.delete()
           messages.success(request, f"{user.username} is no longer an author.")
        except Author.DoesNotExist:
           messages.error(request, f"{user.username} is not an author.")
    


    elif action == 'reject_author':
        try:
           author = Author.objects.get(user=user)
           if not author.is_approved and author.has_applied_for_author:
              author.delete()
              messages.success(request, f"{user.username}'s author application has been rejected.")
           else:
               messages.info(request, f"{user.username} has no pending author application to reject.")
        except Author.DoesNotExist:
            messages.error(request, f"{user.username} has not applied to be an author.")
    return redirect('admin_panel')

@login_required
def banned_action_page(request):
    return render(request, 'banned.html')


def contact(request):
    return render(request, 'about_section/contact.html')

def help(request):
    return render(request, 'about_section/help.html')

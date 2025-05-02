from django.contrib import admin
from django.urls import path,include
from . import views

from .views import *


urlpatterns = [
    #blog
    path('', views.Blog_home, name='blog_home'),
    path('create/', Create_blog, name='create_blog'),
    path('edit/<int:blog_id>/', views.Edit_blog, name='edit_blog'),
    path('delete/<int:blog_id>/', Delete_blog, name='delete_blog'),
    path('blog/<int:blog_id>/', Blog_detail, name='blog_detail'),
    path('category/<str:category>/', views.Blog_home, name='blog_home_by_category'),
    #AUTHOR
    path('create_author/',create_author, name='create_author'),
    path('author_profile/<int:author_id>/', author_profile, name='author_profile'),
    path('author_edit/<int:author_id>/', author_edit,name='author_edit'),
    path('author_delete/<int:author_id>/', author_delete, name='author_delete'),
    path('author_settings/<int:author_id>/', author_setting, name='author_settings'),
    #NORMALAUTHOR
    path('reader/profile/', views.reader_view, name='reader_profile'),
    path('reader/edit/', views.reader_edit, name='reader_edit'),
    path('reader/delete/',views.reader_delete, name='reader_delete'),
    path('reader/settings/', views.reader_setting, name='reader_setting'),
    path('reader/<str:username>/following/', views.reader_following_list, name='reader_following_list'),
    #comments
    path('comment/<str:app_label>/<str:model_name>/<int:object_id>/', views.add_comment, name='add_comment'),
    path('like/<str:app_label>/<str:model_name>/<int:object_id>/', views.toggle_like, name='toggle_like'),
    path('comment/<int:comment_id>/delete/', views.comment_delete, name='comment_delete'),

    #publicview
    path('bookmark/<str:app_label>/<str:model_name>/<int:object_id>/', book_mark, name='book_mark'),
    path('user/<str:username>/', user_profile_redirect, name='user_profile_redirect'),
    path('reader/<str:username>/', views.public_reader_profile, name='public_reader_profile'),
    path('author/<str:username>/', public_author_profile,name='public_author_profile'),
    
    #publicauthor
    path('author/<int:author_id>/follow/', follow_author, name='follow_author'),
    path('author/<int:author_id>/unfollow/', unfollow_author, name='unfollow_author'),
    path('follower-list/<str:username>/', follower_list, name='follower_list'),
    path('following/<str:username>/', following_list, name='following_list'),
    
    #adminpanelview
    path('banned-action/', banned_action_page, name='banned_action_page'),
    path('search/', searchList, name='search_list'),
    path('adminpanel/', adminpanel, name='admin_panel'),
    path('adminpanel/update-user/<int:user_id>/', update_user_status, name='update_user_status'),
    path('adminpanel/edit-user/<int:user_id>/', views.edit_user_status, name='edit_user_status'),
    path('adminpanel/review/<int:user_id>/', views.review_author_application, name='review_author_application'),
    path('adminpanel/<int:user_id>/', views.admin_view_author_profile, name='admin_view_author_profile'),

    path('contact/', views.contact, name='contact'),
    path('help/', views.help, name='help'),
]


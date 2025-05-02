from django.contrib import admin
from . models import Author,Blogpost, ReaderProfile,Comment,PostLikes, BookMark, Follow


# Register your models here.

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display=['user','name', 'profile_photo', 'bio', 'email']
    list_filter=['user']

    def has_profile_photo(self, obj):
        return bool(obj.profile_photo)
    has_profile_photo.short_description = 'Has Profile Photo'

    def approve_author(self, request, queryset):
        queryset.update(is_approved=True,  has_applied_for_author=False)
        self.message_user(request, "Selected users have been approved as authors.")
    approve_author.short_description = "Approve selected authors"

    def reject_author(self, request, queryset):
        queryset.update(is_approved=False, has_applied_for_author=False)
        self.message_user(request, "Selected users have been rejected as authors.")
    reject_author.short_description = "Reject selected authors"

    
@admin.register(ReaderProfile)
class readerAdmin(admin.ModelAdmin):
    list_display=['user', 'gender', 'dob', 'join_date']
    list_filter=['user']



@admin.register(Blogpost)
class blogpostadmin(admin.ModelAdmin):
    list_display=['author', 'title', 'created_at']
    list_filter= ['author']


admin.site.register(Comment)
admin.site.register(PostLikes)

admin.site.register(BookMark)


@admin.register(Follow)
class followadmin(admin.ModelAdmin):
    list_display=['user', 'author','timestamp']
    list_filter=['user']
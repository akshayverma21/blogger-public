from django.db import models
from django.contrib.auth.models import User
from autoslug import AutoSlugField
import uuid
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from django.contrib.contenttypes.fields import GenericRelation
# Create your models here.




class Author(models.Model):
    user=models.OneToOneField(User, on_delete=models.CASCADE)
    name= models.CharField(max_length=50)
    bio= models.TextField(max_length=250)
    profile_photo=models.ImageField(upload_to='authors')
    join_date= models.DateTimeField(auto_now_add=True)
   
    email= models.EmailField(null=True,blank=True)
    email_notifications = models.BooleanField(default=True)
    is_ban=models.BooleanField(default=False)
    has_applied_for_author = models.BooleanField(default=False)
    is_approved=models.BooleanField(default=False)
    is_rejected=models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name}'
    

class Blogpost(models.Model):
    category=(
        ('A', 'ADULT'),
        ('F', 'fiction'),
        ('FT', 'Fantasy'),
        ('Lv', 'Love_story'),
    )

    author=models.ForeignKey(Author, on_delete=models.CASCADE)
    title=models.CharField(max_length=300)
    category_choices= models.CharField(max_length=30, choices=category, default='A')
    content=models.TextField(max_length=4000)
    slug=AutoSlugField(populate_from='title',unique=True, blank=True)
    blog_image=models.ImageField(blank=True, default='')
    comments = GenericRelation('Comment', related_query_name='blogpost')
    likes=GenericRelation('PostLikes',related_query_name='blogpost')
    bookmark=GenericRelation('BookMark',related_query_name='blogpost')
    created_at=models.DateTimeField(auto_now_add=True)

    indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['slug']),
        ]


    def liked_count(self):
        content_type=ContentType.objects.get_for_model(self)
        return PostLikes.objects.filter(content_type=content_type, object_id=self.id).count()
    
    def comment_count(self):
        content_type=ContentType.objects.get_for_model(self)
        return Comment.objects.filter(content_type=content_type, object_id=self.id).count()


    def __str__(self):
        return f'{self.author} {self.title}- {self.category_choices} {self.created_at}'
    


class ReaderProfile(models.Model):
    GENDER_CHOICES=(
        ('M', 'MALE'),
        ('F', 'FEMALE'),
    )

    user=models.OneToOneField(User,on_delete=models.CASCADE)
    name=models.CharField(max_length=50, null=True)
    bio=models.TextField(blank=True)
    dob = models.DateField(null=True, blank=True)  # Date of Birth
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    profile_photo=models.ImageField(upload_to='readers',blank=True, null=True)
    join_date=models.DateTimeField(auto_now_add=True)
    is_ban=models.BooleanField(default=False)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} - {self.gender}'




class Comment(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    body=models.TextField(blank=True)
    content_type=models.ForeignKey(ContentType,on_delete=models.CASCADE) #what model?
    object_id=models.PositiveBigIntegerField() #which item
    content_object=GenericForeignKey('content_type', 'object_id') #give me actual object
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='comment_likes', blank=True)

    def __str__(self):
        return f'{self.body[:30]}...' if len(self.body) > 30 else self.body
    
    class Meta:
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['created_at']),
        ]

    def is_reply(self):
        return self.parent is not None
    
    @property
    def liked_count(self):
        return self.likes.count()
    

    


class PostLikes(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    content_type=models.ForeignKey(ContentType, on_delete=models.CASCADE)
    like=models.BooleanField(default=True)
    object_id=models.PositiveBigIntegerField()
    content_object=GenericForeignKey('content_type', 'object_id')
    parent=models.ForeignKey('self', null=True, blank=True, related_name='likes', on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f'{self.user.username} liked {self.content_object}'
    

class BookMark(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='BookMark')
    content_type=models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id=models.PositiveBigIntegerField()
    content_object=GenericForeignKey('content_type', 'object_id')
    timestamp=models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering=['-timestamp']
        unique_together=['user', 'content_type', 'object_id']

    def __str__(self):
        return f'{self.user.username} bookmarked {self.content_type.model}-{self.content_object}'

class Follow(models.Model):
    user=models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    author=models.ForeignKey(Author, related_name='followers', on_delete=models.CASCADE)
    timestamp=models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'author')


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"
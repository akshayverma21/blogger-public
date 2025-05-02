from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ReaderProfile,Notification, Author
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(post_save, sender=User)
def create_reader_profile(sender, instance, created, **kwargs):
    if created:
        ReaderProfile.objects.create(user=instance)
    else:
        if not hasattr(instance, 'readerprofile'):
            ReaderProfile.objects.create(user=instance)



@receiver(post_save, sender=Author)
def notify_admin_of_application(sender, instance, created, **kwargs):
    if created and instance.has_applied_for_author:
        print(f"New author application from {instance.user.username}")
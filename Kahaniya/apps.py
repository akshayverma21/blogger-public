from django.apps import AppConfig


class KahaniyaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Kahaniya'

    def ready(self):
        import Kahaniya.signals
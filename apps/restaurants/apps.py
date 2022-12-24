from django.apps import AppConfig
from django.db.models.signals import post_save


class RestaurantsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'restaurants'
    
    def ready(self):
        import restaurants.signals
        super().ready()
        from restaurants.models import Review
        post_save.connect(restaurants.signals.update_restaurant_score, sender=Review)
        

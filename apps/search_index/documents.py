from django_elasticsearch_dsl.registries import registry
from django_elasticsearch_dsl import Document, fields
from django.templatetags.static import static

from restaurants.models import Restaurant, Order, RestaurantType


@registry.register_document
class RestaurantDocument(Document):
    restaurant_type = fields.NestedField(properties={
        "name": fields.TextField(),
    })
    restaurant_delivery = fields.NestedField(properties={
        "delivery_fee": fields.IntegerField(),
        "max_distance": fields.IntegerField(),
    })
    opens_at = fields.TextField()
    closes_at = fields.TextField()
    logo = fields.TextField()
    absolute_url = fields.TextField()  
    
    class Index:
        name = 'restaurants'
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }
        
    class Django:
        model = Restaurant
        fields = ['name',
                  'score']
        
    def get_instance_from_related(self, related_instance):
        if isinstance(related_instance, RestaurantType):
            return related_instance.restaurant_type_restaurants
        
    def prepare_logo(self, instance):
        return instance.get_picture_url()
        
    def prepare_opens_at(self, instance):
        return instance.opens_at.isoformat()
        
    def prepare_closes_at(self, instance):
        return instance.closes_at.isoformat()
    
    def prepare_absolute_url(self, instance):
        return instance.get_absolute_url()
        
        
@registry.register_document
class OrderDocument(Document):
    order_repr = fields.TextField()
    
    class Django:
        model = Order
        fields = ["order_number",
                  "order_type",
                  "timestamp"]
        
    class Index:
        name = "restaurant_order"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }
    
    def prepare_order_repr(self, instance):
        return ", ".join(instance.order_repr)
    
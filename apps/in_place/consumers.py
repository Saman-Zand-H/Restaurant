from channels.consumer import AsyncConsumer
from channels.exceptions import StopConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.template.loader import get_template

import json
from typing import NamedTuple
from uuid import UUID
from asgiref.sync import sync_to_async
from logging import getLogger

from restaurants.models import Restaurant, Order
from restaurants.utils import json_custom_decoder
from in_place.utils import (weekly_revenue_chart_data, 
                            weekly_sale_chart_data)
from in_place.views import prepare_order_namedtuple


logger = getLogger(__name__)


class MarkDeliveredConsumer(AsyncConsumer):
    async def close(self, code:int=None):
        if code is not None and code is not True:
            await self.send({"type": "websokcet.close", "code": code})
        else:
            await self.send({"type": "websocket.close"})
    
    async def websocket_connect(self, event):
        self.user = self.scope["user"]
        restaurant = await self.get_restaurant(
            getattr(self.user, "username", ""))
        if restaurant is not None:
            self.group_name = f"mark_done_{restaurant['public_uuid']}"
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.send({
                "type": "websocket.accept"
            })
        else:
            logger.warn(
                f"{self.__class__.__name__} - unauthorized attempt by: "
                f"{getattr(self.user, 'username', 'Anonymous')}")
            await self.close(403)
    
    async def websocket_disconnect(self, event):
        if hasattr(self, "group_name"):
            self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
        raise StopConsumer()
    
    async def websocket_receive(self, event):
        text_data = event.get('text')
        if text_data is not None:
            try:
                data = json.loads(text_data)
                order_uuid = data.get("order")
                done = data.get("done")
                if order_uuid is not None and done is not None:
                    done = await self.change_done(order_uuid, done)
                    ret_data = {
                        "order": order_uuid,
                        "done": done,
                    }
                    
                    await self.channel_layer.group_send(
                        self.group_name,
                        {
                            "type": "ret_done",
                            "msg": ret_data
                        }
                    )
            except:
                pass
            
    async def ret_done(self, event):
        msg = event.get("msg")
        if (
            msg 
            and isinstance(msg, dict)
            and (order := msg.get("order")) is not None
            and await self.validate_uuid(order)
            and (done := msg.get("done")) is not None
        ):
            await self.send(
                {
                    "type": "websocket.send",
                    "msg": json.dumps({"done": done, 
                                       "order": order})
                }
            )
            
    @database_sync_to_async
    def change_done(self, order_uuid, done):
        order = Order.objects.filter(public_uuid=order_uuid)
        if order.exists():
            order.update(done=done)
            return done
        return
            
    @database_sync_to_async
    def get_restaurant(self, username):
        restaurant = Restaurant.objects.filter(
            restaurant_staff__user__username=username)
        if restaurant.exists():
            v = restaurant.values("name", "public_uuid")[0]
            return {"name": v["name"], "public_uuid": v["public_uuid"]}
        return
    
    async def validate_uuid(self, uuid_str):
        try:
            UUID(uuid_str)
            return 1
        except:
            return 0
        

mark_delivered_consumer = MarkDeliveredConsumer.as_asgi()        


class OrdersConsumer(AsyncConsumer):
    async def close(self, code:int=None):
        if code is not None and code is not True:
            await self.send({"type": "websocket.close", "code": code})
        await self.send({"type": "websocket.close"})
        
    async def websocket_connect(self, event):
        self.user = self.scope["user"]
        restaurant = await self.get_restaurant(
            getattr(self.user, "username", ""))
        if restaurant is not None:
            restaurant = restaurant["public_uuid"]
            self.group_name = f"new_item_{restaurant}"
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.send({"type": "websocket.accept"})
        else:
            logger.warn(f"{self.__class__.__name__} - unauthorized attempt by "
                        f" {getattr(self.user, 'username', 'Anonymous')}")
            await self.close(403)
            
    async def websocket_disconnect(self, event):
        if hasattr(self, "group_name"):
            self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
        raise StopConsumer()
    
    async def websocket_receive(self, event):
        text_data = event.get("text")
        if text_data is not None:
            try:
                data = json.loads(text_data)
                required_fields = [
                    "restaurant",
                ]
                required_fields_restaurant = ["public_uuid",
                                              "weekly_revenue",
                                              "weekly_sale"]
                if (
                    all([bool(data.get(i)) 
                         for i in required_fields])
                    and all([bool(data["restaurant"].get(i)) 
                             for i in required_fields_restaurant])
                ):
                    cleaned_data = {i: data.get(i) for i in required_fields}
                    
                    await self.channel_layer.group_send(
                        self.group_name,
                        {
                            "type": "render_new_item",
                            "msg": cleaned_data
                        }
                    )
            except:
                pass
            
    async def render_new_item(self, event):
        msg = event.get("msg")
        if msg is not None and await self.validate_data(msg):
            response = await self.prepare_response(msg=msg,
                                                   user=self.user)
            if response is not None:
                await self.send(
                    {
                        "type": "websocket.send",
                        "text": json.dumps({"response": response})
                    }
                )
            
        else:
            await self.send(
                {
                    "type": "websocket.send",
                    "text": "Invalid."
                }
            )
            
    async def validate_data(self, data: str):
        try:
            data = json.loads(data)
            required_fields = [
                    "restaurant",
                ]
            required_fields_restaurant = ["public_uuid",
                                          "weekly_revenue",
                                          "weekly_sale"]
            if (
                all([bool(data.get(i)) 
                    for i in required_fields])
                and all([bool(data["restaurant"].get(i)) 
                        for i in required_fields_restaurant])
            ):
                return True
        except:
            return False
    
    @database_sync_to_async
    def get_restaurant(self, username):
        restaurant = self.user.user_staff
        if hasattr(self.user, "user_staff"):
            restaurant = self.user.user_staff.restaurant
            return {"name": restaurant.name, 
                    "public_uuid": restaurant.public_uuid}
        return
    
    @database_sync_to_async
    def prepare_response(self, msg, user):
        msg = json.loads(msg)["restaurant"]
        if hasattr(user, "user_staff"):
            restaurant = user.user_staff.restaurant
            orders = prepare_order_namedtuple(restaurant)
            
            weekly_revenue = msg["weekly_revenue"]
            weekly_sale = msg["weekly_sale"]
            revenue_chart, sale_chart = (
                weekly_revenue_chart_data(
                    [i//1000 for i in weekly_revenue]),
                weekly_sale_chart_data(weekly_sale))
                
            template = get_template("in_place/new_item_temp.js")
            context = {
                "orders": orders,
                "revenue_chart": revenue_chart,
                "sale_chart": sale_chart,
                "restaurant": restaurant,
                "user": self.user
            }
            return str(template.render(context))


orders_consumer = OrdersConsumer.as_asgi()

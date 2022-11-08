from elasticsearch_dsl import Q as ESQ
from datetime import datetime
from functools import reduce

class ItemQuery:
    """
    A general class for querying items. 
    For using the classmethods separately, notice that you should pass the
        arguments as key-value pairs.
    """
    def __init__(self, form_values={}):
        self._price_range = {"higher_price": form_values.get("higher_p"),
                             "lower_price" :form_values.get("lower_p")}
        self._min_score = {"score": form_values.get("score")}
        self._is_open = {"is_open": form_values.get("is_open")}
        self._has_free_delivery = {
            "has_free_delivery": form_values.get("free_delivery")}
        self._name_filter = {"name": form_values.get("name")}
        self._cuisine_filter = {"cuisine": form_values.get("cuisine")}
        self._query = self._prepare_queries()

    @property
    def query(self):
        return self._query
    
    def _prepare_queries(self):
        params_names = ["price_range", 
                        "is_open", 
                        "has_free_delivery", 
                        "min_score", 
                        "name_filter",
                        "cuisine_filter"]
        params = [
            self._price_range,
            self._is_open,
            self._has_free_delivery,
            self._min_score,
            self._name_filter,
            self._cuisine_filter
        ]
        q_all = ESQ("match_all")
        params = [*zip(params_names, params)]
        q = [eval(f"{self.__class__.__name__}.{i[0]}(**{i[1]})") for i in params]
        q = reduce(lambda i, j: i & j, q)
        q = q & q_all
        return q
    
    @classmethod
    def price_range(cls, *args, **kwargs):
        gte = kwargs.get("lower_price")
        lte = kwargs.get("higher_price")
        if gte is None and lte is None:
            return ESQ("match_all")
        query = dict()
        if gte:
            query["gte"] = gte
        if lte:
            query["lte"] = lte
        return ESQ("range", price=query)
    
    @classmethod
    def is_open(cls, *args, **kwargs):
        if kwargs.get("is_open"):
            return (ESQ("nested", 
                    path="restaurant", 
                    query=ESQ("range", 
                            restaurant_opens_at={
                                "lte": datetime.now().isoformat()})
                            & ESQ("range", 
                                restaurant__closes_at={
                                    "gte": datetime.now().isoformat()})))    
        return ESQ("match_all")    

    @classmethod
    def has_free_delivery(cls, *args, **kwargs):
        if kwargs.get("has_free_delivery"):
            return ESQ("nested",
                    path="restaurant", 
                    query=ESQ("match",
                            restaurant__delivery__delivery_fee=0))
        return ESQ("match_all")
        
    @classmethod
    def min_score(cls, *args, **kwargs):
        score = kwargs.get("score")
        if isinstance(score, str) and score.isnumeric():
            score = int(score)
        if score and score > 0:
            q = (ESQ("nested", 
                    path="item_reviews",
                    query=ESQ("range", 
                            item_reviews__score={"gte": int(score)})))
        else:
            q = ESQ("match_all")
        return q
        
    @classmethod
    def name_filter(cls, *args, **kwargs):
        name = kwargs.get("name")
        if isinstance(name, str) and bool(name):
            return (ESQ("prefix",
                    name=name)
                    | ESQ("nested", 
                        path="restaurant",
                        query=ESQ("prefix", restaurant__name=name)))
        return ESQ("match_all")

    @classmethod
    def cuisine_filter(cls, *args, **kwargs):
        cuisine = kwargs.get("cuisine")
        if isinstance(cuisine, str) and cuisine != "all":
            return (ESQ("nested", 
                    path="cuisine",
                    query=ESQ("match", cuisine__name=cuisine)))
        return ESQ("match_all")


class RestaurantQuery:
    def __init__(self, form_data=dict()):
        self._min_score = {"score": form_data.get("score")}
        self._is_open = {"is_open": form_data.get("is_open")}
        self._has_free_delivery = {
            "has_free_delivery": form_data.get("free_delivery")}
        self._name_filter = {"name": form_data.get("name")}
        self._query = self._prepare_queries()
    
    @property
    def query(self):
        return self._query

    def _prepare_queries(self):
        params_names = ["is_open", 
                        "has_free_delivery", 
                        "min_score", 
                        "name_filter",]
        params = [
            self._is_open,
            self._has_free_delivery,
            self._min_score,
            self._name_filter,
        ]
        q_all = ESQ("match_all")
        params = [*zip(params_names, params)]
        q = [eval(f"{self.__class__.__name__}.{i[0]}(**{i[1]})") for i in params]
        q = reduce(lambda i, j: i & j, q)
        q = q & q_all
        return q

    @classmethod
    def is_open(cls, *args, **kwargs):
        if kwargs.get("is_open"):
            return (ESQ("range", opens_at={
                "lte": datetime.now().time().isoformat()})
                    & ESQ("range", closes_at={
                        "gte": datetime.now().time().isoformat()}))   
        return ESQ("match_all")    

    @classmethod
    def has_free_delivery(cls, *args, **kwargs):
        if kwargs.get("has_free_delivery"):
            return ESQ("nested",
                    path="delivery", 
                    query=ESQ("match",
                              delivery__delivery_fee=0))
        return ESQ("match_all")
        
    @classmethod
    def min_score(cls, *args, **kwargs):
        score = kwargs.get("score")
        if isinstance(score, str) and score.isnumeric():
            score = int(score)
        if score and score > 0:
            q = ESQ("range", score={"gte": score})
        else:
            q = ESQ("match_all")
        return q
        
    @classmethod
    def name_filter(cls, *args, **kwargs):
        name = kwargs.get("name")
        if isinstance(name, str) and bool(name):
            return ESQ("prefix", name=name)
        return ESQ("match_all")


class OrderQuery:
    def __init__(self, form_data=dict()):
        self.timestamp = form_data.get("timestamp")
        self.keyword = form_data.get("keyword")
        self._query = self._prepare_queries()
        
    @property
    def query(self):
        return self._querz

    def _prepare_queries(self):
        params_names = ["timestamp", 
                        "keyword"]
        params = [
            self._timestamp,
            self._keyword
        ]
        q_all = ESQ("match_all")
        params = [*zip(params_names, params)]
        q = [eval(f"{self.__class__.__name__}.{i[0]}(**{i[1]})") for i in params]
        q = reduce(lambda i, j: i & j, q)
        q = q & q_all
        return q
    
    def timestamp(self, *args, **kwargs):
        timestamp = kwargs.get("timestamp")
        if timestamp:
            return ESQ("match_all", timestamp=timestamp)
        return ESQ("match_all")
    
    def keyword(self, *args, **kwargs):
        keyword = kwargs.get("keyword")
        if keyword:
            return ESQ("multi_match",
                       query=keyword,
                       fields=["order_repr", 
                               "description", 
                               "order_number"])
        return ESQ("match_all")

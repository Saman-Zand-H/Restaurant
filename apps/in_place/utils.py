from datetime import datetime, timedelta
from persiantools.jdatetime import JalaliDate
from typing import NamedTuple, List
from django.utils import timezone
from django.db.models import F
from itertools import groupby, chain
from operator import is_not, attrgetter
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
from math import ceil, floor

from restaurants.models import Restaurant
from delivery.models import DeliveryCartItem, DeliveryCart


class ChartData(NamedTuple):
        labels: str
        values: str
        high: int
        low: int = 0


def weekly_sale_chart_data(weekly_sale: List[int]):
    """
    prepares data to be sent to the chart on the client side.

    Args:
        weekly_sale: a list containing weekly sales data.

    Returns:
        a namedtuple containing the labels, the values
            , the higher bound and the lower bound.
    """

    labels = reversed(
        [
            (
                JalaliDate(
                    datetime.now() - timedelta(days=i))
                .ctime()
                .split(" ")[0][0]
            )
            for i in range(7)
        ]
    )
    values = weekly_sale
    low = floor(min(values))
    # To keep a little space at the top of the chart
    high = ceil(max(values) + 5)
    values = [str(i) for i in weekly_sale]
    return ChartData("-".join(labels), 
                     "-".join(values), 
                     high=high, 
                     low=low)


def weekly_score_chart_data(weekly_score: List[int]):
    """
    prepares data to be sent to the chart on the client side.

    Args:
        weekly_score: a list containing the weekly scores data.

    a namedtuple containing the labels, the values
            , the higher bound and the lower bound.
    """

    labels = reversed(
        [
            (
                JalaliDate(
                    datetime.now() - timedelta(days=i))
                .ctime()
                .split(" ")[0][0]
            )
            for i in range(7)
        ]
    )
    values = weekly_score
    # To keep a little space at the top of the chart
    high = 6
    values = [str(i) for i in weekly_score]
    return ChartData("-".join(labels), 
                     "-".join(values), 
                     high=high)


def weekly_revenue_chart_data(weekly_revenue: List[int]):
    """
    prepares data to be sent to the chart on the client side.

    Args:
        weekly_revenue: a list containing the weekly revenue data.

    Returns:
        a namedtuple containing the labels, the values
            , the higher bound and the lower bound.
    """

    labels = reversed(
        [
            (
                JalaliDate(
                    datetime.now() - timedelta(days=i))
                .ctime()
                .split(" ")[0][0]
            )
            for i in range(7)
        ]
    )
    values = weekly_revenue
    low = floor(min(values))
    # To keep a little space at the top of the chart
    high = ceil(max(values) + 5)
    values = [f"{i}" for i in weekly_revenue]
    
    return ChartData("-".join(labels), 
                     "-".join(values), 
                     high=high, 
                     low=low)


def get_restaurant_sales(restaurant_id: int):
    restaurant = Restaurant.objects.filter(id=restaurant_id)
    if restaurant.exists():
        restaurant = restaurant.first()
        return restaurant.all_revenues
    return []


def sales_gamma(restaurant_id: int):
    """evaluate sell data for a gamma distribution.

    Args:
        restaurant_id (int): restaurant instance id of the instance under inspection.

    Returns:
        dict:
            x: sells
            y: probabilty of the sell occurance
            stdev: the standard deviation
            mean: the mean
            q1: the first quantile value
            q3: the third qunatile value
    """
    sells = [i[1] for i in get_restaurant_sales(restaurant_id)]
    data = {"x": [], "y": [], "stdev": [], "mean": [], "med": [], "q1": [], "q3": []}
    if sells:
        s, loc, scale = stats.gamma.fit(sells)
        q1, med, q3 = (
            np.quantile(sells, 0.25),
            np.median(sells),
            np.quantile(sells, 0.75),
        )
        x = np.linspace(min(sells), max(sells))
        f = stats.gamma.pdf(x, s, loc, scale)
        data.update(
            {
                "x": [*x],
                "y": [*f],
                "stdev": np.std(sells),
                "mean": np.mean(sells),
                "q1": q1,
                "q3": q3,
                "med": med,
            }
        )
    return data


def reg_data(restaurant_id, day_interval: int = 30):
    """returs the data used for plotting the linear regression
       of the restaurant's sells.

    Args:
        restaurant_id (int): id of the instance
        day_interval (int, optional): date interval used. Defaults to 30.

    Returns:
        _type_: a dict containing {
            "r_x": x values for regression,
            "r_y": calculated regression f(x),
            "s": array: [{"x": "actual x values", "y": "actual y values"}]
            "r2": coefficient of determination of regression,
            "mse": mean squared_error of the regression
        }
    """
    restaurant = Restaurant.objects.filter(id=restaurant_id)
    if restaurant.exists():
        restaurant = restaurant.first()
        t = timezone.now()
        x = [t - timedelta(i) for i in range(day_interval)]
        sales = [restaurant.get_daily_revenue(i) for i in x]
        x = [i.timestamp() for i in x]
        model = LinearRegression().fit(np.asarray(x).reshape(-1, 1), np.asarray(sales))
        r_c, r_i = model.coef_[0], model.intercept_
        r_x = [*np.linspace(min(x), max(x))]
        r_f = lambda i: i * r_c + r_i
        r_y = [r_f(i) for i in r_x]
        return {
            "r_x": r_x,
            "r_y": r_y,
            "s": [{"x": i, "y": j} for i, j in zip(x, sales)],
            "r2": r2_score(sales, [r_f(i) for i in x]),
            "mse": mean_squared_error(sales, [r_f(i) for i in x]),
        }
    return {"r_x": [], "r_y": [], "s": {"x": [], "y": []}}


def orders_geos(restaurant_id: int):
    """Return The spatial data of every delivery order submitted
       for a specific restaurant, identified by its id.

    Args:
        restaurant_id (int): id of the restaurant instance

    Returns:
        Dict[list]: a dict of a list of lat and lon
    """
    deliv_qs = DeliveryCartItem.objects.filter(
        item__item__cuisine__restaurant__id=restaurant_id
    ).annotate(deliv_cart=F("cart"))
    grouped = [*map(lambda i: i[0], groupby(deliv_qs, attrgetter("deliv_cart")))]
    points = [
        *filter(
            lambda i: is_not(i, None),
            [DeliveryCart.objects.get(id=i).user_address for i in grouped],
        )
    ]
    points = [*chain.from_iterable([i.location.coords for i in points])]
    return {"lon": [i for i in points[::2]], "lat": [j for j in points[1::2]]}

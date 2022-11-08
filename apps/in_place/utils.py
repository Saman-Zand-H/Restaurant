from datetime import datetime, timedelta
from persiantools.jdatetime import JalaliDate
from typing import NamedTuple, List
from math import ceil

from restaurants.models import Restaurant


def weekly_sale_chart_data(weekly_sale:List[int]):
    """
    prepares data to be sent to the chart on the client side.
    
    Args:
        weekly_sale: a list containing weekly sales data.
        
    Returns: 
        a namedtuple containing the labels, the values
            , the higher bound and the lower bound.
    """
    class ChartData(NamedTuple):
        labels: str
        values: str
        high: int
        low: int = 0
        
    labels = reversed(
        [JalaliDate(datetime.now()-timedelta(days=i)).ctime().split(" ")[0][0] for i in range(7)])
    values = weekly_sale
    # To keep a little space at the top of the chart
    high = ceil(max(values) + 5)
    values = [str(i) for i in weekly_sale]
    return ChartData("-".join(labels), "-".join(values), high=high)


def weekly_score_chart_data(weekly_score:List[int]):
    """
    prepares data to be sent to the chart on the client side.
    
    Args:
        weekly_score: a list containing the weekly scores data.
        
    a namedtuple containing the labels, the values
            , the higher bound and the lower bound.
    """
    class ChartData(NamedTuple):
        labels: str
        values: str
        high: int
        low: int=1
        
    labels = reversed(
        [JalaliDate(datetime.now()-timedelta(days=i)).ctime().split(" ")[0][0] for i in range(7)])
    values = weekly_score
    # To keep a little space at the top of the chart
    high = 6
    values = [str(i) for i in weekly_score]
    return ChartData("-".join(labels), "-".join(values), high=high)
    
    
def weekly_revenue_chart_data(weekly_revenue:List[int]):
    """
    prepares data to be sent to the chart on the client side.
    
    Args:
        weekly_revenue: a list containing the weekly revenue data.
        
    Returns: 
        a namedtuple containing the labels, the values
            , the higher bound and the lower bound.
    """
    class ChartData(NamedTuple):
        labels: str
        values: str
        high: int
        low: int=0
    
    labels = reversed(
        [JalaliDate(datetime.now()-timedelta(days=i)).ctime().split(" ")[0][0] for i in range(7)])
    values = weekly_revenue
    # To keep a little space at the top of the chart
    high = ceil(max(values) + 5)
    values = [f"{i}" for i in weekly_revenue]
    return ChartData("-".join(labels), "-".join(values), high=high)
    
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from restaurants.models import Restaurant
from in_place.utils import (
    weekly_revenue_chart_data,
    weekly_sale_chart_data,
    weekly_score_chart_data,
    get_restaurant_sales,
    sales_gamma,
    reg_data,
    orders_geos,
)


chart_response = {
    status.HTTP_200_OK: openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "labels": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING),
                description="labels for chart",
            ),
            "values": openapi.Schema(
                type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_NUMBER)
            ),
            "high": openapi.Schema(type=openapi.TYPE_NUMBER),
            "low": openapi.Schema(type=openapi.TYPE_NUMBER),
        },
    )
}


def instance_exists(val, model, field_name: str = "id"):
    if val is not None:
        return model.objects.filter(**{field_name: val}).exists()


class RevenueChartView(APIView):
    @swagger_auto_schema(responses=chart_response)
    def get(self, request, *args, **kwargs):
        val = kwargs.get("id")
        if instance_exists(val=val, model=Restaurant):
            restaurant = Restaurant.objects.get(id=val)
            data = weekly_revenue_chart_data(restaurant.weekly_revenue)._asdict()
            data.update(
                {
                    "labels": data["labels"].split("-"),
                    "values": [int(i) for i in data["values"].split("-")],
                }
            )
            return Response(data, status=status.HTTP_200_OK)


revenue_chart_view = RevenueChartView.as_view()


class SalesChartView(APIView):
    @swagger_auto_schema(responses=chart_response)
    def get(self, request, *args, **kwargs):
        val = kwargs.get("id")
        if instance_exists(val=val, model=Restaurant):
            restaurant = Restaurant.objects.get(id=val)
            data = weekly_sale_chart_data(restaurant.weekly_sale)._asdict()
            return Response(data, status=status.HTTP_200_OK)


sales_chart_view = SalesChartView.as_view()


class ScoreChartView(APIView):
    @swagger_auto_schema(responses=chart_response)
    def get(self, request, *args, **kwargs):
        val = kwargs.get("id")
        if instance_exists(val, Restaurant):
            restaurant = Restaurant.objects.get(id=val)
            data = weekly_score_chart_data(restaurant.weekly_score)._asdict()
            return Response(data, status=status.HTTP_200_OK)


score_chart_view = ScoreChartView.as_view()


class SalesView(APIView):
    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                ),
                description="an array, containing the total sale grouped by date.",
            )
        },
    )
    def get(self, request, *args, **kwargs):
        val = kwargs.get("id")
        if instance_exists(val, Restaurant):
            data = get_restaurant_sales(restaurant_id=val)
            return Response(data, status=status.HTTP_200_OK)


sales_view = SalesView.as_view()

sales_gamma_response = {
    status.HTTP_200_OK: openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "x": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                description="amount of sale.",
                items=openapi.Items(type=openapi.TYPE_NUMBER),
            ),
            "y": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                description="estimated probability of sale.",
                items=openapi.Items(type=openapi.TYPE_NUMBER),
            ),
            "stdev": openapi.Schema(
                type=openapi.TYPE_NUMBER, description="standard deviation of sales."
            ),
            "mean": openapi.Schema(
                type=openapi.TYPE_NUMBER, description="the mean of sales."
            ),
            "q1": openapi.Schema(
                type=openapi.TYPE_NUMBER,
                description="the first quantile of the sales.",
            ),
            "med": openapi.Schema(
                type=openapi.TYPE_NUMBER, description="median of the sales."
            ),
            "q3": openapi.Schema(
                type=openapi.TYPE_NUMBER,
                description="the third quantile of the sales.",
            ),
        },
    )
}


class GammaChartView(APIView):
    @swagger_auto_schema(responses=sales_gamma_response)
    def get(self, request, *args, **kwargs):
        val = kwargs.get("id")
        if instance_exists(val, Restaurant):
            data = sales_gamma(val)
            return Response(data, status=status.HTTP_200_OK)


gamma_chart_view = GammaChartView.as_view()


regression_response = {
    status.HTTP_200_OK: openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "r_x": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                description="x values for regression",
                items=openapi.Items(type=openapi.TYPE_NUMBER),
            ),
            "r_y": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                description="calculated regression f(x)",
                items=openapi.Items(type=openapi.TYPE_NUMBER),
            ),
            "s": openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "x": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        description="actual x values",
                        items=openapi.Items(type=openapi.TYPE_NUMBER),
                    ),
                    "y": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        description="actual y values.",
                        items=openapi.Items(type=openapi.TYPE_NUMBER),
                    ),
                },
            ),
            "r2": openapi.Schema(
                type=openapi.TYPE_NUMBER,
                description="R^2 (coefficient of determination of regression)",
            ),
            "mse": openapi.Schema(
                type=openapi.TYPE_NUMBER,
                description="MSE (Mean Squared Error of regression)",
            ),
        },
    )
}


class RegressionView(APIView):
    @swagger_auto_schema(responses=regression_response)
    def get(self, request, *args, **kwargs):
        val = kwargs.get("id")
        if instance_exists(val, Restaurant):
            data = reg_data(val)
            return Response(data, stauts=status.HTTP_200_OK)


regression_view = RegressionView.as_view()


class OrdersCoordsView(APIView):
    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "lat": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Items(type=openapi.TYPE_NUMBER),
                    ),
                    "lon": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Items(type=openapi.TYPE_NUMBER),
                    ),
                },
            )
        }
    )
    def get(self, request, *args, **kwargs):
        val = kwargs.get("id")
        if instance_exists(val, Restaurant):
            data = orders_geos(val)
            return Response(data, status=status.HTTP_200_OK)


orders_coords_view = OrdersCoordsView.as_view()

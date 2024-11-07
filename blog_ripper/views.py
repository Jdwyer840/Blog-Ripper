from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from .controllers.blog_processor import BlogProcessor


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
# @permission_classes([IsAuthenticated])
def my_view_func(request: Request) -> Response:
    """if this function is called the following should happen
    1) Request should have RBA or MGO
    2) Use a controller to fetch the blog information and process it
    3) use jinja2 for templating

    """
    result = BlogProcessor(number_of_posts=10).process()
    data = {
        "message": "Processing successful",
        "data": {}
    }

    return Response(data)

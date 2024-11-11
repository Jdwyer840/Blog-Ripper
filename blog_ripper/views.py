import logging

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from .controllers.blog_processor import BlogProcessor

satellite_feed = logging.getLogger('satellite_feed')


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
# @permission_classes([IsAuthenticated])
def rip_blogs(request: Request) -> Response:
    satellite_feed.info("Starting to rip some blogs.")
    """if this function is called the following should happen
    1) Request should have RBA or MGO
    2) Use a controller to fetch the blog information and process it
    3) use jinja2 for templating
    4) we need a cron runner
    5) Models for the posts, we should have a system that validates
    The raw post data should have some identifiers. we date and the brand should be enough
    We should also check for matching elements in the html. 
    We can start adding selector classes or something like that.

    """
    logger = logging.getLogger('satellite_feed')
    logger.debug('This is a DEBUG message')
    logger.info('This is an INFO message')
    logger.warning('This is a WARNING message')
    logger.error('This is an ERROR message')
    logger.critical('This is a CRITICAL message')
    try:
        BlogProcessor(number_of_posts=10).process()
        data = {
            "message": "Processing successful",
            "data": {}
        }
    except Exception as e:
        satellite_feed.error(f"Something went wrong rippin' blogs {str(e)}")
        return Response({"status": "ERROR", "message": f"Something went wrong processing the blogs. {str(e)}"})

    return Response(data)

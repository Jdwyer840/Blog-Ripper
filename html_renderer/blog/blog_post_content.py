from utilities.common import CoreUtilities
from utilities.wordpress_post import COOPBlogPost
from html_renderer.base import BaseTemplate


import datetime


class BlogPostContent(BaseTemplate):

    template = "/blog/blog_post_content.html"

    def __init__(self, blog_post_obj: COOPBlogPost = None):
        # might need to do this when saving the date, or even do this in the blog processr. dates should be good to go in here.
        post_date_str_fmt = CoreUtilities.extract_date_format_from_date_str(blog_post_obj.date)
        post_date = CoreUtilities.datetime_str_reformat(blog_post_obj.date, post_date_str_fmt, "%m-%d-%y")
        self.context = blog_post_obj.__dict__
        self.context.update({'date': post_date})


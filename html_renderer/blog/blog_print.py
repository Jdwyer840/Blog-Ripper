from utilities.wordpress_post import COOPBlogPost
from html_renderer.base import BaseTemplate


class BlogPrint(BaseTemplate):

    template = "blog/print.html"

    def __init__(self, data: COOPBlogPost):
        self.context = data.__dict__

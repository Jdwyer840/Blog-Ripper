from utilities.wordpress_post import COOPBlogPost
from html_renderer.base import BaseTemplate


class BlogPost(BaseTemplate):

    template = "/blog/post.html"

    def __init__(self, data: COOPBlogPost):
        super().__init__(self.template, data.__dict__)

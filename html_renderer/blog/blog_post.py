from utilities.wordpress_post import WordPressPost
from html_renderer.base import BaseTemplate


class BlogPost(BaseTemplate):

    template = "/blog/post.html"

    def __init__(self, data: WordPressPost):
        super().__init__(self.template, data.__dict__)

from utilities.wordpress_post import COOPBlogPost
from html_renderer.base import BaseTemplate


class BlogPrint(BaseTemplate):

    template = "blog/print.html"

    def __init__(self, data: COOPBlogPost):
        # TODO
        super().__init__(self.template, data.__dict__)
        # self.data = data
        # self.rendered_html = self.process_html()

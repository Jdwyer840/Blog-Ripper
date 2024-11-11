from utilities.wordpress_post import WordPressPost
from html_renderer.base import BaseTemplate


class BlogPrint(BaseTemplate):

    template = "blog/print.html"

    def __init__(self, data: WordPressPost):
        # TODO
        super().__init__(self.template, data.__dict__)
        # self.data = data
        # self.rendered_html = self.process_html()

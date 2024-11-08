from blog_ripper.utils.wordpress_post import WordPressPost
from html_renderer.base import BaseTemplate


class RABPost(BaseTemplate):

    template = "template/RAB/post.html"

    def __init__(self, data: WordPressPost):
        # TODO
        super().__init__(self.template, data.__dict__)
        # self.data = data
        # self.rendered_html = self.process_html()

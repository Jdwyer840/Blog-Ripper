from jinja2 import Template

from blog_ripper.utils.wordpress_post import WordPressPost


class RABPost(Template):

    template = "template/RAB/post.html"

    def __init__(self, data: WordPressPost):
        self.data = data
        self.rendered_html = self.process_html()

    def process_html(self):
        print()
from html_renderer.blog.blog_post_content import BlogPostContent
from blog_ripper.models import COOPBlogPost
from html_renderer.base import BaseTemplate


class BlogPost(BaseTemplate):

    template = "/blog/post.html"

    def __init__(self, data: COOPBlogPost):
        self.context = data.to_dict()
        self.context.update({
            "post_content": BlogPostContent(data).render()
        })

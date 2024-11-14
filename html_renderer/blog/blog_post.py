from html_renderer.blog.blog_post_content import BlogPostContent
from utilities.wordpress_post import COOPBlogPost
from html_renderer.base import BaseTemplate


class BlogPost(BaseTemplate):

    template = "/blog/post.html"

    def __init__(self, data: COOPBlogPost):
        self.context = data.__dict__
        self.context.update({
            "post_content": BlogPostContent(data).render()
        })

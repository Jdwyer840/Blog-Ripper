from html_renderer.blog.blog_post import BlogPost
from html_renderer.blog.blog_post_content import BlogPostContent
from blog_ripper.models import COOPBlogPost
from html_renderer.base import BaseTemplate


class BlogMain(BaseTemplate):

    template = "/blog/main.html"

    def __init__(self, blog_post_objs: list[COOPBlogPost] = None, blog_post_html_strs: list[str] = None):
        self.context = {
            'blog_posts': blog_post_html_strs if blog_post_html_strs else self._render_blog_post_html_list_from_post_objs(blog_post_objs)
        }

    @staticmethod
    def _render_blog_post_html_list_from_post_objs(blog_post_objs: list[COOPBlogPost]) -> list[str]:
        return [BlogPostContent(blog_post_obj).render() for blog_post_obj in blog_post_objs]

import os

from jinja2 import Template, Environment, FileSystemLoader
from typing import Optional

from blog_ripper import settings


class BaseTemplate:

    context: Optional[dict] = None

    env = Environment(loader=FileSystemLoader(os.path.join(settings.BASE_DIR, 'templates')))

    def __init__(self, template_path: str, context: dict = None):
        self.template = self.env.get_template(template_path)
        self.context = context or {}

    def render(self) -> str:
        return self.template.render(self.context)

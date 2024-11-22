import logging
import os

from jinja2 import Template, Environment, FileSystemLoader
from typing import Optional

from blog_ripper import settings


class BaseTemplate:

    context: Optional[dict] = None
    jinja_twoplate: Optional[Template] = None
    template: Optional[str] = None

    satellite = logging.getLogger('satellite_feed')
    env = Environment(loader=FileSystemLoader(os.path.join(settings.BASE_DIR, 'templates')), enable_async=True)
    # env.filters['render'] = str

    # def __init__(self, template_path: str, context: dict = None):

    # self.context = context or {}

    def render(self) -> str:
        if not self.template:
            self.satellite.error('Subclass must initialize the field "template"')
        self.jinja_twoplate = self.env.get_template(self.template)
        return self.jinja_twoplate.render(self.context)

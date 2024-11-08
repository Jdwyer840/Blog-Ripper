from jinja2 import Template
from typing import Optional

from blog_ripper import settings


class BaseTemplate(Template):

    context: Optional[dict] = None

    def __init__(self, template_path: str, context: dict = None):
        super().__init__(self._load_template(template_path))
        self.context = context

    def render(self) -> str:
        return super().render(**self.context)

    @staticmethod
    def _load_template(template_file: str) -> str:
        """Reads the template file and returns its content as a string."""
        path = f'{settings.BASE_DIR}/templates/{template_file}'
        with open(path, "r") as file:
            return file.read()

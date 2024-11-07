from jinja2 import Template
import typing as t


class HtmlRenderer(Template):

    def __init__(self, file_path: str, data: t.Any):
        super().__init__()
        self.file_path = file_path
        self.data = data

    # def render(self, *args: t.Any, **kwargs: t.Any) -> str:
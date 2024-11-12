# from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
# @dataclass


class COOPBlogPost:
    plan_url: Optional[str] = None
    wordpress_post_id: Optional[int] = None
    brand: Optional[str] = None
    print_url: Optional[str] = None
    date_created: Optional[datetime] = None
    title: Optional[str] = None
    plan_image: Optional[str] = None
    paragraph1: Optional[str] = None
    paragraph2: Optional[str] = None
    paragraph3: Optional[str] = None
    paragraph4: Optional[str] = None
    date: Optional[datetime] = None

    def __init__(self, data: dict = None):
        if data:
            self.plan_url = data.get("plan_url")
            self.brand = data.get("brand")
            self.print_url = data.get("print_url")
            self.date_created = data.get("date_created")
            self.title = data.get("title")
            self.plan_image = data.get("plan_image")
            self.paragraph1 = data.get("paragraph1")
            self.paragraph2 = data.get("paragraph2")
            self.paragraph3 = data.get("paragraph3")
            self.paragraph4 = data.get("paragraph4")
            self.date = data.get("date")


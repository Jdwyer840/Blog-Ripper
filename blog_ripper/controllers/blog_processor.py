import datetime
import json
import os
import re
from typing import Optional
from urllib.request import urlretrieve

from bs4 import BeautifulSoup
import requests

from .. import settings
from ..utils.wordpress_post import WordPressPost


class BlogProcessor:

    def __init__(self, number_of_posts: int = 11):
        self.url = "https://promotions.coopconnect.com/wp-json/wp/v2/posts/"
        self.number_of_posts = number_of_posts

        self.posts_response: Optional[list[dict]] = None
        self.posts = []
        self.mode = 'RAB'

    def process(self):
        self._fetch_post_data()
        self._build_post_objects()
        # TODO after the blogs are processed
        # TODO 1) make the print html files
        # TODO 2) then the blogs need to be written to the main html file.
        # TODO 3) models for the posts?

    def _write_blog_posts_details_files(self) -> None:
        print()
        for post in self.posts:
            print('use the jinja templates and file thing. just')

    def _build_post_objects(self):
        seen_brands = []
        i = 0
        for data in self.posts_response:
            post = WordPressPost()
            post.title = data.get('title')
            brand = re.sub(r'\d+', '', post.title.split(" ")[0])
            if brand not in seen_brands:
                # make sure this works the same as the code in c#
                seen_brands.append(brand)
            else:

                seen_brands.append(f"{brand}{i}")

            post.date = data.get('date')  # make proper data time
            post_html_str: str = data.get('content', {}).get('rendered')
            soup = BeautifulSoup(post_html_str.replace("&nbsp;", "&#160;"), "html.parser")
            p_tags = soup.findAll('p')
            for idx, tag in enumerate(p_tags):
                if idx == 0:
                    post.paragraph1 = str(tag)
                elif idx == 1:
                    post.paragraph2 = str(tag)
                elif idx == 2:
                    post.paragraph3 = self.replace_links(str(tag))
                elif idx >= 3:
                    paragraph_4_html = "".join(str(tag) for tag in p_tags[3:])
                    post.paragraph4 = self.replace_links(paragraph_4_html)
                    break

            # TODO Image Gathering and naming the html / shtml files.
            start_of_week_date = self.get_monday_of_current_week()
            post.plan_url = f"{start_of_week_date}_{brand}_{'.html' if self.mode == 'RAB' else '.shtml'}"
            post.print_url = f"{start_of_week_date}_{brand}_print{'.html' if self.mode == 'RAB' else '.shtml'}"

            post.title = title.replace('<br>', '')
            if len(p_tags) > 0 and len(p_tags[0].contents) <= 2:
                first_child = p_tags[0].contents[0]
                # Check if the first child has attributes and if it’s a tag (like an <img>)
                if hasattr(first_child, 'attrs') and 'src' in first_child.attrs:
                    post.plan_image = first_child['src']
                    # plan_image = first_child['src']
            if post.plan_image:
                post.plan_image = f"images/{self.download_post_image(post, start_of_week_date)}"
            self.posts.append(post)



    def download_post_image(self, post_data: WordPressPost, post_date: datetime.datetime):
        image_name = f"{post_date}_{post_data.brand}_promo.png"
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
                    # download image to this path)
        urlretrieve(post_data.plan_image, temp_dir)

        return image_name
        # public string ImageDownload(string imgURL, string brand, string path, string date)
        # {
        #     var imageString = date + "_" + brand + "_promo.png";
        #     if (!Directory.Exists(path))
        #     {
        #         Directory.CreateDirectory(path);
        #     }
        #     using (WebClient client = new WebClient())
        #     {
        #         client.DownloadFile(new Uri(imgURL), path + "\\" + imageString);
        #     }
        #     return imageString;
        # }


    def get_monday_of_current_week(self) -> datetime.datetime:
        # Monday is the start of the week with datetime.datetime
        today = datetime.today()
        start_of_week = 0  # Monday is 0 in Python's weekday()
        diff = (today.weekday() - start_of_week) % 7
        return today - datetime.timedelta(days=diff)


    def replace_links(self, str_to_replace_links: str) -> str:
        # Compile the regex pattern to find plan_id
        expression = re.compile(r"http.*app\.coopconnect\.com.*plan_id=(?P<plan_id>[0-9]*)")
        results = list(expression.finditer(str_to_replace_links))

        # Default link_id if no match is found
        link_id = "0"
        if results:
            # Get the last plan_id found
            link_id = results[-1].group("plan_id")

        # Set link replacement URL with padded link_id
        link_replacement_str = f"http://rab.recas.com/coop_search/search.mp?show_plan={link_id.zfill(6)}&schema=u&schema1=y\""

        # Define the replacement pattern and apply re.sub
        pattern = r"http.*app\.coopconnect\.com.*plan_id=(\d*).*\""
        source = re.sub(pattern, lambda: self.local_replace_match_case(link_replacement_str), str_to_replace_links, flags=re.IGNORECASE)
        return source

    def local_replace_match_case(self, replace_with: str) -> str:
        # Check if the replacement should be capitalized
        if replace_with and replace_with[0].isupper():
            return replace_with.capitalize()
        else:
            return replace_with

    # container_div = soup.find("div", id="container")
    #
    # # Find all <p> tags within this div
    # p_tags = container_div.find_all("p")
    #
    # # Get the second <p> tag (index 1 since indexing starts from 0)
    # second_p = p_tags[1].text
    # print(second_p)
    def _fetch_post_data(self):
        # this hsould also save to a table the post data, so we can use it to reference
        response = requests.get(self.url)
        response.raise_for_status()
        self.posts_response = response.json()
        print(json.dumps(self.posts_response, indent=4))


# Installing collected packages: urllib3, idna, charset-normalizer, certifi, requests
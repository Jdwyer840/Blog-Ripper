import datetime
import html
import logging
import os
import re
from typing import Optional
from urllib.request import urlretrieve

from bs4 import BeautifulSoup
import requests

from html_renderer.blog.blog_post import BlogPost
from html_renderer.blog.blog_print import BlogPrint
from .. import settings
from utilities.wordpress_post import WordPressPost


class BlogProcessor:

    def __init__(self, number_of_posts: int = 11):
        self.url = "https://promotions.coopconnect.com/wp-json/wp/v2/posts/"
        self.number_of_posts = number_of_posts

        self.posts_response: Optional[list[dict]] = None
        self.posts = []
        self.mode = 'RAB'
        self.seen_brands_count_map = {}
        self.satellite_feed = logging.getLogger('satellite_feed')
        self.satellite_feed.error('UH OH TEST')
        self._build_file_path()

    def process(self):
        self._fetch_post_data()
        self._build_post_objects()
        # TODO maybe name these better
        self._write_blog_posts_html()
        # TODO after the blogs are processed
        # TODO 1) make the print html files DONE
        # TODO 2) then the blogs need to be written to the main html file.
        # TODO 3) models for the posts?

    def _build_file_path(self) -> None:
        mode_folder = 'RAB' if self._is_mode_rab() else 'MGO'
        date_str = datetime.datetime.today().strftime('%m%d%y')  # Corrected strftime format
        self.html_to_upload_file_path = os.path.join(settings.MEDIA_ROOT, mode_folder, date_str)
        os.makedirs(self.html_to_upload_file_path, exist_ok=True)

    def _is_mode_rab(self) -> bool:
        return self.mode == "RAB"

    def _write_blog_posts_html(self) -> None:
        # using (FileStream fs = new FileStream(path + "\\" + date + "_" + Posts.Brand + type, FileMode.Create))
        try:
            for post in self.posts:
                # Construct the directory path, separate from the file name
                directory_path = self.html_to_upload_file_path
                os.makedirs(directory_path, exist_ok=True)

                # Join the directory with the filename
                # post_file_path = os.path.join(directory_path, post.plan_url)

                # Write to the file (post_file_path is now a full file path)
                with open(os.path.join(directory_path, post.plan_url), 'w') as file:
                    file.write(BlogPost(post).render())
                with open(os.path.join(directory_path, post.print_url), 'w') as file:
                    file.write(BlogPrint(post).render())


        except Exception as e:
            self.satellite_feed.error(f"Blogs fucked up: {str(e)}")
            raise

    def _build_post_objects(self):
        for data in self.posts_response:
            post = WordPressPost()
            # TODO maybe make the true safe get function
            post.title = html.unescape(data.get('title', {}).get('rendered', '').replace('<br>', ''))
            post.brand = re.sub(r'\W+', '', post.title.split(" ")[0]).lower()
            if post.brand not in self.seen_brands_count_map.keys():
                # make sure this works the same as the code in c#
                self.seen_brands_count_map[post.brand] = 1
            else:
                self.seen_brands_count_map[post.brand] += 1
                post.brand = f"{post.brand}{self.seen_brands_count_map[post.brand]}"

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
            start_of_week_date = self.get_monday_of_current_week_date_str()
            # TODO is plan url the right name ?
            post.plan_url = f"{start_of_week_date}_{post.brand}{'.html' if self.mode == 'RAB' else '.shtml'}"
            post.print_url = f"{start_of_week_date}_{post.brand}_print{'.html' if self.mode == 'RAB' else '.shtml'}"

            if len(p_tags) > 0 and len(p_tags[0].contents) <= 2:
                first_child = p_tags[0].contents[0]
                # Check if the first child has attributes and if it’s a tag (like an <img>)
                if hasattr(first_child, 'attrs') and 'src' in first_child.attrs:
                    post.plan_image = first_child['src']
                    # plan_image = first_child['src']
            if post.plan_image:
                post.plan_image = f"images/{self.download_post_image(post, start_of_week_date)}"

            self.posts.append(post)

    def download_post_image(self, post_data: WordPressPost, post_date: str) -> str:
        image_name = f"{post_date}_{post_data.brand}_promo.png"
        image_path = os.path.join(self.html_to_upload_file_path, image_name)
        urlretrieve(post_data.plan_image, image_path)

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

    # def get_monday_of_current_week_date_str(self) -> str:
    #     # Monday is the start of the week with datetime.datetime
    #     today = datetime.datetime.today()
    #     start_of_week = 0  # Monday is 0 in Python's weekday()
    #     diff = (today.weekday() - start_of_week) % 7
    #     return (today - datetime.timedelta(days=diff)).strftime('%m%d%y')

    def get_monday_of_current_week_date_str(self) -> str:
        # Monday is the start of the week with datetime.datetime
        return datetime.datetime.today().strftime('%m%d%y')

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
        source = re.sub(pattern, lambda _: self.local_replace_match_case(link_replacement_str), str_to_replace_links, flags=re.IGNORECASE)
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
        self.satellite_feed.info('Fetching posts')
        response = requests.get(f'{self.url}?per_page={self.number_of_posts}')
        response.raise_for_status()
        self.posts_response = response.json()
        self.satellite_feed.info('Posts fetched')

        # print(json.dumps(self.posts_response, indent=4)s)


# Installing collected packages: urllib3, idna, charset-normalizer, certifi, requests
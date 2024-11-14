import datetime
import html
import logging
import os
import re
from typing import Optional
from urllib.request import urlretrieve

from bs4 import BeautifulSoup  # noqa
import requests

from html_renderer.blog.blog_main import BlogMain
from html_renderer.blog.blog_post import BlogPost
from html_renderer.blog.blog_print import BlogPrint
from .. import settings
from utilities.wordpress_post import COOPBlogPost


class BlogProcessor:

    def __init__(self, number_of_posts: int = 12):
        self.url = "https://promotions.coopconnect.com/wp-json/wp/v2/posts/"
        self.number_of_posts = number_of_posts

        self.posts_response: Optional[list[dict]] = None
        self.posts = []
        self.mode = 'MGO'
        self.seen_brands_count_map = {}
        self.satellite_feed = logging.getLogger('satellite_feed')
        self.satellite_feed.error('UH OH TEST')
        self._build_file_path()

    def process(self):
        self._fetch_wordpress_post_data()
        self._build_coop_post_objects()
        self._write_coop_blog_posts_linked_html_files()
        # TODO 2) then the blogs need to be written to the main html file.

    def _fetch_wordpress_post_data(self) -> None:
        self.satellite_feed.info('Fetching posts')
        response = requests.get(f'{self.url}?per_page={self.number_of_posts}')
        response.raise_for_status()
        self.posts_response = response.json()
        self.satellite_feed.info('Posts fetched')

    def _build_coop_post_objects(self) -> None:
        for ripped_wp_post in self.posts_response:
            coop_post = COOPBlogPost()
            self._rip_title_date_post_id_from_wordpress_post(ripped_wp_post=ripped_wp_post, coop_post=coop_post)
            self._rip_and_process_brand_data_from_wordpress_post(coop_post=coop_post)
            self._rip_paragraphs_and_plan_image_from_wordpress_post(wordpress_post_data=ripped_wp_post, coop_post=coop_post)
            self._rip_html_and_image_urls_from_wordpress_post(coop_post=coop_post)
            self.posts.append(coop_post)

    def _write_coop_blog_posts_linked_html_files(self) -> None:
        main_posts: list[COOPBlogPost] = []
        try:
            for post in self.posts:
                directory_path = self.html_to_upload_file_path
                os.makedirs(directory_path, exist_ok=True)
                post_html = BlogPost(post).render()
                with open(os.path.join(directory_path, post.plan_url), 'w') as file:
                    file.write(post_html)
                with open(os.path.join(directory_path, post.print_url), 'w') as file:
                    file.write(BlogPrint(post).render())
                main_posts.append(post)
            with open(os.path.join(self.html_to_upload_file_path, 'blog_main.html'), 'w') as file:
                file.write(BlogMain(blog_post_objs=main_posts).render())
        except Exception as e:
            # TODO cat errors for a post ? maybe have an error field in thepost model
            self.satellite_feed.error(f"Blogs fucked up: {str(e)}")
            raise e

    def _rip_title_date_post_id_from_wordpress_post(self, ripped_wp_post: dict,  coop_post: COOPBlogPost) -> None:
        title_raw = ripped_wp_post.get('title', {}).get('rendered', '')
        coop_post.title = html.unescape(re.sub(r'<.*?>', '', title_raw))
        # coop_post.title = html.unescape(ripped_wp_post.get('title', {}).get('rendered', '').replace('<br>', '').replace('<h2>', '').replace('</h2>', ''))
        coop_post.date = ripped_wp_post.get('date')
        coop_post.wordpress_post_id = ripped_wp_post.get('id')
        if not coop_post.wordpress_post_id:
            # TODO this assumes there will always be a post id.
            self.satellite_feed.warning(f'No wordpress post id. Post info \n\nTitle: {coop_post.title}\n\nPost date {coop_post.date}')

    def _rip_and_process_brand_data_from_wordpress_post(self, coop_post: COOPBlogPost) -> None:
        coop_post.brand = re.sub(r'\W+', '', coop_post.title.split(" ")[0]).lower()
        if coop_post.brand not in self.seen_brands_count_map.keys():
            # make sure this works the same as the code in c#
            self.seen_brands_count_map[coop_post.brand] = 1
        else:
            self.seen_brands_count_map[coop_post.brand] += 1
            coop_post.brand = f"{coop_post.brand}{self.seen_brands_count_map[coop_post.brand]}"

    def _rip_html_and_image_urls_from_wordpress_post(self, coop_post: COOPBlogPost) -> None:
        start_of_week_date = self._get_today_mmddyy_date_str()
        coop_post.plan_url = f"{start_of_week_date}_{coop_post.brand}{'.html' if self.mode == 'RAB' else '.shtml'}"
        coop_post.print_url = f"{start_of_week_date}_{coop_post.brand}_print{'.html' if self.mode == 'RAB' else '.shtml'}"

        if coop_post.plan_image:
            coop_post.plan_image = f"images/{self._download_post_image(coop_post, start_of_week_date)}"

    def _rip_paragraphs_and_plan_image_from_wordpress_post(self, wordpress_post_data: dict, coop_post: COOPBlogPost) -> None:
        post_html_str: str = wordpress_post_data.get('content', {}).get('rendered')
        soup = BeautifulSoup(post_html_str.replace("&nbsp;", "&#160;"), "html.parser")
        p_tags = soup.findAll('p')
        self._rip_paragraph_data_from_wordpress_post(coop_post, p_tags)
        self._rip_plan_image_data_from_wordpress_post_p_tags(coop_post, p_tags)

    def _rip_paragraph_data_from_wordpress_post(self, post: COOPBlogPost, wp_p_tags) -> None:
        for idx, tag in enumerate(wp_p_tags):
            if idx == 0:
                post.paragraph1 = tag.text
            elif idx == 1:
                post.paragraph2 = str(tag)
            elif idx == 2:
                post.paragraph3 = self._replace_links(str(tag))
            elif idx >= 3:
                paragraph_4_html = "".join(str(tag) for tag in wp_p_tags[3:])
                post.paragraph4 = self._replace_links(paragraph_4_html)
                break

    @staticmethod
    def _rip_plan_image_data_from_wordpress_post_p_tags(post: COOPBlogPost, wp_p_tags: list) -> None:
        if len(wp_p_tags) > 0 and len(wp_p_tags[0].contents) <= 2:
            first_child = wp_p_tags[0].contents[0]
            if hasattr(first_child, 'attrs') and 'src' in first_child.attrs:
                post.plan_image = first_child['src']

    def _build_file_path(self) -> None:
        mode_folder = 'RAB' if self._is_mode_rab() else 'MGO'
        date_str = datetime.datetime.today().strftime('%m%d%y')
        self.html_to_upload_file_path = os.path.join(settings.MEDIA_ROOT, mode_folder, date_str)
        os.makedirs(self.html_to_upload_file_path, exist_ok=True)

    def _is_mode_rab(self) -> bool:
        return self.mode == "RAB"

    def _download_post_image(self, post_data: COOPBlogPost, post_date: str) -> str:
        image_name = f"{post_date}_{post_data.brand}_promo.png"
        try:
            image_path = os.path.join(self.html_to_upload_file_path, image_name)
            urlretrieve(post_data.plan_image, image_path)
        except Exception as e:
            self.satellite_feed.error(str(e))
            self.satellite_feed.info('ERROROR')
        return image_name

    @staticmethod
    def _get_today_mmddyy_date_str() -> str:
        return datetime.datetime.today().strftime('%m%d%y')

    def _replace_links(self, str_to_replace_links: str) -> str:
        # Compile the regex pattern to find plan_id
        expression = re.compile(r"http.*app\.coopconnect\.com.*plan_id=(?P<plan_id>[0-9]*)")
        results = list(expression.finditer(str_to_replace_links))

        link_id = "0"
        if results:
            link_id = results[-1].group("plan_id")

        link_replacement_str = f"http://rab.recas.com/coop_search/search.mp?show_plan={link_id.zfill(6)}&schema=u&schema1=y\""
        pattern = r"http.*app\.coopconnect\.com.*plan_id=(\d*).*\""
        source = re.sub(pattern, lambda _: self._local_replace_match_case(link_replacement_str), str_to_replace_links, flags=re.IGNORECASE)
        return source

    @staticmethod
    def _local_replace_match_case(replace_with: str) -> str:
        # Check if the replacement should be capitalized
        if replace_with and replace_with[0].isupper():
            return replace_with.capitalize()
        else:
            return replace_with

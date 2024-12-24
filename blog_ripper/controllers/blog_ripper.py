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
from utilities.common import CoreUtilities
from .. import settings
from blog_ripper.models import COOPBlogPost


class BlogRipper:
    """TODO <img src="/blog/images/091318_shaw_promo.jpg" align="right" width="288">  this here appears to be the last date of a post
    TODO  have command pass in a date range. if date range is far apart, no worries, will either need to write to the main file potentially in increments.
     TODO so we will need to instead of overwrite, use some html package to insert new post data into the file.
     TODO probably another method that will call process in a loop, might need some flags or something, but the main thing is there will need to be some new method that writes to the main blog file."""

    DEFAULT_WORDPRESS_URL: str = "https://promotions.coopconnect.com/wp-json/wp/v2/posts/"
    DEFAULT_WORDPRESS_URL_DATE_RANGE: str = "https://promotions.coopconnect.com/wp-json/wp/v2/posts?after=2023-09-01T00:00:00&before=2023-12-01T00:00:00"

    def __init__(self, mode: str = 'RAB', number_of_posts: int = 13, date_range: tuple[datetime.datetime, datetime.datetime] = None, blog_ripper_config: dict = None):
        self.blogripper_config = blog_ripper_config if blog_ripper_config is not None else {}
        self.url = self.blogripper_config.get('wordpress_url') or self.DEFAULT_WORDPRESS_URL
        print(self.url)
        self.number_of_posts = number_of_posts
        self.posts_response: Optional[list[dict]] = None
        self.posts: list[COOPBlogPost] = []
        self.mode = 'MGO'
        self.seen_brands_count_map = {}
        self.satellite_feed = logging.getLogger('satellite_feed')
        self.satellite_feed.error('UH OH TEST')
        self.errors = []
        self.success_count = 0
        self._build_file_path()

    def process(self):
        try:
            self._fetch_wordpress_post_data()
            self._build_coop_post_objects()
            self._write_coop_blog_posts_linked_html_files()
            self._save_post_data()
        except Exception as e:
            self._handle_error(f'Processing blogs jobs failed {str(e)}')

    def process_with_date_range(self, start_date: datetime.datetime, end_date: datetime.datetime, step_days: int = 7):
        current_date = start_date
        while current_date < end_date:
            next_date = min(current_date + datetime.timedelta(days=step_days), end_date)
            try:
                self._fetch_posts_by_date_range(current_date, next_date)
                self._build_coop_post_objects()
                self._write_coop_blog_posts_linked_html_files()
                self._save_post_data()
                self.success_count += len(self.posts)
            except Exception as e:
                self._handle_error(f"Failed to process range {current_date} to {next_date}: {str(e)}")
            current_date = next_date

    def _fetch_posts_by_date_range(self, start_date: datetime.datetime, end_date: datetime.datetime):
        url = f'{self.url}?after={start_date.isoformat()}&before={end_date.isoformat()}&per_page={self.number_of_posts}'
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = 'utf-8'
        self.posts_response = response.json()
        self.satellite_feed.info(f'Fetched posts from {start_date} to {end_date}')

    def _fetch_wordpress_post_data(self) -> None:
        self.satellite_feed.info('Fetching posts')
        response = requests.get(f'{self.url}?per_page={self.number_of_posts}')
        response.raise_for_status()
        response.encoding = 'utf-8'
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
        self._write_post_and_print_html()
        self._write_main_blog_html()

    def _write_post_and_print_html(self) -> None:
        for post in self.posts:
            try:
                self._write_html_file(post.plan_url, BlogPost(post).render())
                self._write_html_file(post.print_url, BlogPrint(post).render())
            except Exception as e:
                self._handle_error(f"ERROR: Failed to write html or shtml post or print html files.\nBlog ID: {post.wordpress_post_id} \nBlog Title: {post.title} \nError Message: {str(e)}")

    def _handle_error(self, err_msg: str) -> None:
        self.errors.append(err_msg)
        self.satellite_feed.error(err_msg)

    # def _write_main_blog_html(self) -> None:
    #     try:
    #         self._write_html_file('blog_main.html', BlogMain(blog_post_objs=self.posts).render())
    #     except Exception as e:
    #         self._handle_error(f"ERROR: Failed to write main blog html content \nError Message: {str(e)}")

    def _write_main_blog_html(self) -> None:
        try:
            main_file_path = os.path.join(self.html_to_upload_file_path, 'blog_main.html')
            if os.path.exists(main_file_path):
                # Load existing content
                with open(main_file_path, 'r', encoding='utf-8') as file:
                    existing_html = file.read()

                # Parse the existing HTML with BeautifulSoup
                soup = BeautifulSoup(existing_html, "html.parser")
                container_div = soup.find("div", {"id": "container"})

                # Render new content and parse it
                new_content = BlogMain(blog_post_objs=self.posts).render()
                new_soup = BeautifulSoup(new_content, "html.parser")

                # Insert new content at the top of the container
                if container_div:
                    container_div.insert(0, new_soup)

                    # Save updated file
                    with open(main_file_path, 'w', encoding='utf-8') as file:
                        file.write(str(soup))
                else:
                    raise ValueError("Container div with id 'container' not found in HTML!")
            else:
                # Create a new file if it doesn't exist
                self._write_html_file('blog_main.html', BlogMain(blog_post_objs=self.posts).render())
        except Exception as e:
            self._handle_error(f"ERROR: Failed to update main blog HTML content \nError Message: {str(e)}")

    def _save_post_data(self) -> None:
        pass
        # for post in self.posts:
        #     post.save()

    def _write_html_file(self, filename: str, post_html: str) -> None:
        CoreUtilities.write_file(file_path=os.path.join(self.html_to_upload_file_path, filename), mode='w', content=post_html, encoding='utf-8')

    def _rip_title_date_post_id_from_wordpress_post(self, ripped_wp_post: dict,  coop_post: COOPBlogPost) -> None:
        title_raw = ripped_wp_post.get('title', {}).get('rendered', '')
        title_raw = str(title_raw)
        title_trimmed = title_raw.split('<br>', 1)[0]
        coop_post.title = html.unescape(re.sub(r'<.*?>', '', title_trimmed))
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
                post.paragraph3 = self._sanitize_wordpress_hyperlinks(str(tag))
            elif idx >= 3:
                paragraph_4_html = "".join(str(tag) for tag in wp_p_tags[3:])
                post.paragraph4 = self._sanitize_wordpress_hyperlinks(paragraph_4_html)
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
            self._handle_error(f"ERROR: could not download image.\nBlog ID: {post_data.wordpress_post_id}\nBlog Title: {post_data.title}\nError Message: {str(e)}")
        return image_name

    @staticmethod
    def _get_today_mmddyy_date_str() -> str:
        # return datetime.datetime.today().strftime('%m%d%y')
        yesterday = datetime.datetime.today() - datetime.timedelta(days=1)
        return yesterday.strftime('%m%d%y')

    def _sanitize_wordpress_hyperlinks(self, str_to_replace_links: str) -> str:
        # Compile the regex pattern to find plan_id
        expression = re.compile(r"http.*app\.coopconnect\.com.*plan_id=(?P<plan_id>[0-9]*)")
        results = list(expression.finditer(str_to_replace_links))

        link_id = "0"
        if results:
            link_id = results[-1].group("plan_id")

        link_replacement_str = f"http://rab.recas.com/coop_search/search.mp?show_plan={link_id.zfill(6)}&schema=u&schema1=y\""
        pattern = r"http.*app\.coopconnect\.com.*plan_id=(\d*).*\""
        source = re.sub(pattern, lambda _: self._make_hyper_link_have_consistent_casing(link_replacement_str), str_to_replace_links, flags=re.IGNORECASE)
        return source

    @staticmethod
    def _make_hyper_link_have_consistent_casing(replace_with: str) -> str:
        # Check if the replacement should be capitalized
        if replace_with and replace_with[0].isupper():
            return replace_with.capitalize()
        else:
            return replace_with

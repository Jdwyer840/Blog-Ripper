from django.core.management.base import BaseCommand

from blog_ripper.controllers.blog_ripper import BlogRipper


class Command(BaseCommand):
    help = 'Description of your command'
    mode_choices = ['rab', 'mgo']

    def add_arguments(self, parser):
        # Define command-line arguments here
        parser.add_argument('mode', type=str, choices=self.mode_choices, help='The choice')
        parser.add_argument('amount', type=int, default=12, help='The amount of blogs to retrieve')

    def handle(self, *args, **options):
        number_of_posts_to_query
        BlogRipper()

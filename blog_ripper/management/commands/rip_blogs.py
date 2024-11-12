from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Description of your command'
    mode_choices = ['rab', 'mgo']

    def add_arguments(self, parser):
        # Define command-line arguments here
        parser.add_argument('mode', type=str, choices=self.mode_choices, help='The choice')

    def handle(self, *args, **options):
        sample_arg = options['mode']
        self.stdout.write(self.style.SUCCESS(f'Successfully processed argument: {sample_arg}'))

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from apps.blog.management.commands.factory import UserFactory, ArticleFactory, CategoryFactory


class Command(BaseCommand):
    '''
        This is a simple management file to populate the database with some dummy data.
    '''

    def add_arguments(self, parser):
        parser.add_argument('--users',
            default=10,
            type=int,
            help='The number of fake users to create.')

    def handle(self, *args, **options):
      self.stdout.write(self.style.SUCCESS("Started database population process..."))
      for _ in range(options['users']):
         UserFactory.create()
      CategoryFactory.create_batch(5)
      ArticleFactory.create_batch(20)

      self.stdout.write(self.style.SUCCESS("Successfully populated the database."))
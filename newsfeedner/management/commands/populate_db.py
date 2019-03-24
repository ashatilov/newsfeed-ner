from django.core.management.base import BaseCommand

from newsfeedner.utils import FeedDownloader, generate_wordcloud


class Command(BaseCommand):
    help = 'Populate db'

    def handle(self, *args, **options):
        downloader = FeedDownloader()
        downloader.get_feeds()
        downloader.get_articles()
        downloader.get_entities()

        generate_wordcloud('./newsfeedner/static/newsfeedner')


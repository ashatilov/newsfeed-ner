import os
from django.conf import settings
from newsfeedner.utils import FeedDownloader, generate_wordcloud


def update_feeds(project_path):
    downloader = FeedDownloader()
    downloader.get_feeds()
    downloader.get_articles()
    downloader.get_entities()

    generate_wordcloud(os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT))

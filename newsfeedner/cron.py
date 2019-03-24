import os
from newsfeedner.utils import FeedDownloader, generate_wordcloud


def update_feeds(project_path):
    downloader = FeedDownloader()
    downloader.get_feeds()
    downloader.get_articles()
    downloader.get_entities()

    generate_wordcloud(os.path.join(project_path, 'newsfeedner/static/newsfeedner'))

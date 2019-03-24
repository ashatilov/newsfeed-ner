import feedparser
import requests
from bs4 import BeautifulSoup

import os
import pytz
from time import mktime, struct_time
import datetime

from deeppavlov import build_model, configs
import pymorphy2
from transliterate import translit

from wordcloud import WordCloud
import matplotlib
matplotlib.use('Agg')
    
from django.db.models import Count
from django.utils import timezone

from newsfeedner.models import Feed, Article, Entity, FeedEntities


# dictionary with links to rss feed sources
FEED_URLS = {
    # information agencies
    'ria': 'https://ria.ru/services/lenta/more.html?&onedayonly=1&articlemask=lenta_common',
    'tass': 'http://tass.ru/rss/v2.xml',
    'interfax': 'https://www.interfax.ru/rss.asp',
    'rbc': 'http://static.feed.rbc.ru/rbc/logical/footer/news.rss',
    'ura.news': 'https://ura.news/rss',
    'regnum': 'https://regnum.ru/rss/news',
    'rosbalt': 'http://www.rosbalt.ru/feed/',

    # papers
    'izvestia': 'https://iz.ru/xml/rss/all.xml',
    'kommersant': 'https://www.kommersant.ru/RSS/news.xml',
    'vedomosti': 'https://www.vedomosti.ru/rss/news',
    'rg': 'https://rg.ru/xml/index.xml',
    'kp': 'http://kp.ru/rss/allsections.xml',
    'mk': 'https://www.mk.ru/rss/index.xml',
    'novayagazeta': 'https://content.novayagazeta.ru/rss/all.xml',
    'nezavisimayagazeta': 'http://www.ng.ru/rss/',
    'aif': 'http://www.aif.ru/rss/all.php',
    'pg': 'https://www.pnp.ru/rss/index.xml',
    'argumenti': 'http://argumenti.ru/rss/argumenti_online.xml',

    # tv
    # '1tv': '',  # no feed
    'vesti': 'https://www.vesti.ru/vesti.rss',
    'rentv': 'http://ren.tv/export/feed.xml',
    # 'ntv': '',  # no feed
    '5kanal': 'https://www.5-tv.ru/news/rss/',
    'tvrain': 'https://tvrain.ru/export/rss/all.xml',
    'zvezda': 'https://tvzvezda.ru/export/rss.xml',
    'tvcentr': 'https://www.tvc.ru/RSS/news.ashx',

    # radio
    # 'govoritmoskva': '',  # too many different feeds
    'echo': 'https://echo.msk.ru/news.rss',
    'svoboda': 'https://www.svoboda.org/api/z-pqpiev-qpp',
    'bfm': 'https://www.bfm.ru/news.rss?type=news',

    # internet (if not mentioned above and has rss feed)
    'rt': 'https://russian.rt.com/rss',
    'meduza': 'https://meduza.io/rss/all',
    'lenta': 'https://lenta.ru/rss',
    'gazeta.ru': 'https://www.gazeta.ru/export/rss/lenta.xml',
    'fontanka': 'https://www.fontanka.ru/fontanka.rss',
    'znak.com': 'https://www.znak.com/rss',
    'life.ru': 'https://life.ru/xml/feed.xml?hashtag=%D0%BD%D0%BE%D0%B2%D0%BE%D1%81%D1%82%D0%B8',
    'dni.ru': 'https://dni.ru/rss.xml',
    'vz.ru': 'https://vz.ru/rss.xml',
    'theins.ru': 'https://theins.ru/feed',
    'newizv.ru': 'https://newizv.ru/rss',
    'zona.media': 'https://zona.media/rss',
    'pravda.ru': 'https://www.pravda.ru/export.xml',
    'takiedela': 'https://takiedela.ru/news/feed/',
    'newtimes.ru': 'https://newtimes.ru/rss/',
}

# list of words, which will not be counted as entities
STOPWORDS = ['СМИ']

# TODAY - midnight Moscow time
MSK = pytz.timezone('Europe/Moscow')


def get_today_midnight():
    today = timezone.localtime(timezone=MSK).replace(hour=0, minute=0, second=0, microsecond=0)
    return today


def generate_wordcloud(filepath):
    '''
    Function for creating wordcloud pictures of current day entities.
    '''

    today = get_today_midnight()
    query_today = FeedEntities.objects.filter(
        article__published_parsed__gt=today)
    query_ent = (query_today.values('ent', 'ent__name', 'ent__entity_class')
                            .annotate(entities_count=Count('ent'))
                            .order_by('-entities_count'))

    colormaps = {
        'PER': 'summer',
        'ORG': 'winter',
        'LOC': 'autumn',
    }

    for class_ in ['PER', 'LOC', 'ORG']:
        freqs = {i['ent__name']: i['entities_count'] for i in query_ent
                 if (i['ent__entity_class'] == class_) and (i['ent__name'] not in STOPWORDS)}

        wordcloud = WordCloud(font_path=os.path.join(filepath, 'helveticaneue.otf'), width=800, height=600, margin=1,
                              background_color='white', min_font_size=6,
                              mode='RGB', colormap=colormaps[class_], max_words=100,
                              collocations=False, normalize_plurals=False).generate_from_frequencies(freqs)
        wordcloud.to_file(os.path.join(filepath, f'wc-{class_}.png'))


class Morpher:
    '''
    Class for converting words to normal form.
    '''

    def __init__(self):
        self.morph = pymorphy2.MorphAnalyzer()

    def normalize(self, word):
        if word.isupper():
            return word

        p = self.morph.parse(word)[0]
        word_nominative = p.inflect({'nomn'})

        if word_nominative:
            word_norm = word_nominative.word
        else:
            word_norm = p.normal_form

        # convert to initial letter case
        if word.islower():
            result = word_norm
        elif word.isupper():
            result = word_norm.upper()
        else:
            result = word_norm.capitalize()
        return result


class NerModel:
    '''
    Named Entity Recognition model class.
    '''

    def __init__(self):
        self.model = build_model(configs.ner.ner_rus, download=True)

    def run(self, sentence):
        if isinstance(sentence, str):
            sentence = [sentence]
        return self.model(sentence)


class RIAparser:
    """
    Class to parse https://ria.ru/ news - no access to rss feed.
    Returns result with same fields which will be used later as feedparser result.
    """
    def get(self, url):
        """
        TODO: add retry when status_code != 200
        """
        r = requests.get(url)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, features='html.parser')
        return soup

    
    def parse(self, feed_url):
        result = {
            'feed': {
                'title': 'РИА Новости',
            },
            'href': feed_url,
            'entries': []
        }
        
        soup = self.get(feed_url)
        if not soup:
            return result
        
        d_now = datetime.datetime.now(tz=pytz.timezone('Europe/Moscow'))
        
        for item in soup.find_all('div', {'class': 'list-item'}):
            feed_item = {
                'title': None,
                'published_parsed': None,
                'link': None,
                'id': None,
            }
            id_data = item.find('a', {'class': 'list-item__content'})
            id_ = id_data.get('href').split('.')[0].replace('/', '')
            feed_item['id'] = id_

            data = item.find('span', {'class': 'share'})
            feed_item['title'] = data.get('data-title')
            feed_item['link'] = data.get('data-url')
            
            time_data = item.find('div', {'class': 'list-item__date'}).text
            if ',' in time_data:
                time_data = time_data.split(',')[1]
            h, m = [int(i) for i in time_data.split(':')]
            d_item = d_now
            if (0 <= d_now.hour < 3) and (20 < h <= 23):
                d_item = d_item.replace(day=d_item.day-1)
            d_item = d_item.replace(hour=h).replace(minute=m).astimezone(pytz.timezone('UTC'))
            feed_item['published_parsed'] = struct_time(d_item.timetuple())
            
            result['entries'].append(feed_item)
        return result


class FeedDownloader:
    '''
    Main class for feed downloads and database updates.
    Used in cron jobs for periodical updates.
    '''

    def __init__(self, feed_urls=FEED_URLS):
        self.feed_urls = feed_urls
        self.rss_raw = {}

        # Get new data (if any) from feed sources
        for key in self.feed_urls:
            if key == 'ria':
                self.rss_raw[key] = RIAparser().parse(self.feed_urls[key])
            else:
                self.rss_raw[key] = feedparser.parse(self.feed_urls[key])

        self.ner_model = NerModel()
        self.morpher = Morpher()

    def parse_ner_result(self, result):
        """
        Parse result of ner model.
        Returns parsed sentence as a list of dicts:
            [
                {
                    'ent_class': str ('PER'|'LOC'|'ORG'|'O'),
                    'words': str (entity words together or None for 'O'),
                    'entity': str (entity words together normalized or None for 'O'),
                    'entity_translit': str (transliterated entity or None for 'O'),
                },
                ...
            ]
        """
        current_dict = None
        sentence_parsed = []

        for word, (i, tag) in zip(result[0][0] + ['<END>'], enumerate(result[1][0] + ['O'])):
            if '-' in tag:
                # if entity - clear from punctuation
                word = word.strip()
                for char in ['«', '»', '`' '"', "'"]:
                    word = word.replace(char, '')

                position, entity_class = tag.split('-')
                if position == 'B':
                    if current_dict:
                        sentence_parsed.append(current_dict)
                    word_normalized = self.morpher.normalize(word)
                    current_dict = {
                        'entity_class': entity_class,
                        'entity': word_normalized,
                        'words': word,
                        'entity_translit': (translit(word_normalized, 'ru', reversed=True)
                                            .replace(' ', '-').replace("'", "_").replace('/', '-'))
                    }
                elif position == 'I' and current_dict:
                    word_normalized = self.morpher.normalize(word)
                    current_dict['entity'] += (' ' + word_normalized)
                    current_dict['words'] += (' ' + word)
                    current_dict['entity_translit'] = (translit(current_dict['entity'], 'ru', reversed=True)
                                                       .replace(' ', '-').replace("'", "_").replace('/', '-'))
            elif tag == 'O':
                if current_dict:
                    sentence_parsed.append(current_dict)
                    current_dict = None
                sentence_parsed.append(
                    {'entity_class': tag, 'words': word, 'entity': None, 'entity_translit': None})
        return sentence_parsed[:-1]

    def get_feeds(self):
        '''
        Create or update feeds data.
        '''
        for feed in self.rss_raw:
            feed_name = self.rss_raw[feed]['feed']['title']
            feed_url = self.rss_raw[feed]['href']
            time_now = timezone.now()

            new_feed, created = Feed.objects.get_or_create(
                name=feed_name,
                url=feed_url,
                defaults={'last_fetched_at': time_now},
            )

            new_feed.last_fetched_at = time_now
            new_feed.save()

    def get_articles(self):
        '''
        Update feeds article data.
        '''
        new_articles = []
        for feed in self.rss_raw:
            for article in self.rss_raw[feed]['entries']:
                if article:
                    feed_name = self.rss_raw[feed]['feed']['title']
                    feed_id = Feed.objects.get(name=feed_name)
                    url = article['link']
                    id_in_feed = article.get('id', url)
                    title = article['title']
                    title = title.replace('"', '')  # remove " for NER convenience
                    published_parsed = datetime.datetime.fromtimestamp(mktime(article['published_parsed']),
                                                                    tz=pytz.timezone('UTC'))

                    if not Article.objects.filter(feed=feed_id, id_in_feed=id_in_feed).exists():
                        new_article = Article(
                            feed=feed_id,
                            id_in_feed=id_in_feed,
                            url=url,
                            title=title,
                            title_json=None,
                            published_parsed=published_parsed,
                        )
                        new_articles.append(new_article)

        Article.objects.bulk_create(new_articles)

    def get_entities(self):
        '''
        Recognize unparsed titles' entities, update database.
        '''
        articles_to_parse = Article.objects.filter(is_entities_parsed=False)

        for article in articles_to_parse:
            print(article.title)
            result = self.ner_model.run(article.title)
            title_parsed = self.parse_ner_result(result)
            article_entities = [i for i in title_parsed if i['entity']]

            if article_entities:
                for d in article_entities:
                    entity_name = d['entity']
                    entity_translit = d['entity_translit']
                    entity_class = d['entity_class']
                    entity_words = d['words']

                    new_entity, created = Entity.objects.get_or_create(
                        name=entity_name,
                        name_translit=entity_translit,
                        entity_class=entity_class,
                    )

                    new_feed_entity, created = FeedEntities.objects.get_or_create(
                        ent=new_entity,
                        words=entity_words,
                    )
                    article.article_entities.add(new_feed_entity)

            article.title_json = title_parsed
            article.is_entities_parsed = True
            article.save()


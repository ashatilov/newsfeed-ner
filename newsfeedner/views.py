from django.views.generic import ListView, TemplateView
from django.db.models import Q, Count
from django.utils import timezone

from .models import Feed, Article, Entity, FeedEntities
from .utils import STOPWORDS, MSK, get_today_midnight


class MainPage(ListView):
    template_name = 'newsfeedner/main_page.html'
    context_object_name = 'mainpage_data'

    paginate_by = 20
    n_entities = 5

    today = get_today_midnight()
    queryset = Article.objects.filter(published_parsed__gt=today)

    def get_ent_dict(self):
        query_today = FeedEntities.objects.filter(article__published_parsed__gt=self.today)
        query_ent = (query_today.values('ent', 'ent__name', 'ent__name_translit', 'ent__entity_class')
                                .exclude(ent__name__in=STOPWORDS)
                                .annotate(entities_count=Count('ent'))
                                .order_by('-entities_count'))

        query_per = query_ent.filter(ent__entity_class='PER')[:self.n_entities]
        query_org = query_ent.filter(ent__entity_class='ORG')[:self.n_entities]
        query_loc = query_ent.filter(ent__entity_class='LOC')[:self.n_entities]

        query_dict = {
            'per': query_per,
            'org': query_org,
            'loc': query_loc,
        }
        return query_dict

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entities_dict'] = self.get_ent_dict()
        context['last_fetched_at'] = (Feed.objects.order_by('-last_fetched_at').all()[0]
                                                  .last_fetched_at.astimezone(MSK)
                                                  .strftime("%H:%M:%S"))
        return context


class EntityDetail(ListView):
    template_name = 'newsfeedner/entity_detail.html'
    context_object_name = 'entity_data'
    paginate_by = 20

    today = get_today_midnight()

    def get_queryset(self):
        entities = Entity.objects.filter(name_translit=self.kwargs['entity'])
        self.entity_name = entities[0].name
        queryset = Article.objects.filter(Q(published_parsed__gt=self.today) &
                                          Q(article_entities__ent__in=entities))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entity_name'] = self.entity_name
        return context


class EntityClassList(ListView):
    template_name = 'newsfeedner/ent_class.html'
    context_object_name = 'ent_class_data'
    paginate_by = 20

    today = get_today_midnight()

    def get_queryset(self):
        query_today = FeedEntities.objects.filter(article__published_parsed__gt=self.today)
        queryset = (query_today.values('ent', 'ent__name', 'ent__name_translit', 'ent__entity_class')
                               .exclude(ent__name__in=STOPWORDS)
                               .annotate(entities_count=Count('ent'))
                               .order_by('-entities_count')
                               .filter(ent__entity_class=self.kwargs['ent_class']))
        return queryset

    def get_context_data(self, **kwargs):
        ent_class_names = {
            'PER': 'персоны',
            'LOC': 'локации',
            'ORG': 'организации',
        }
        context = super().get_context_data(**kwargs)
        ent_class = self.kwargs['ent_class']
        context['ent_class'] = ent_class
        context['ent_class_name'] = ent_class_names[ent_class]
        context['wc_image'] = f'newsfeedner/wc-{ent_class}.png'
        return context


class WordClouds(TemplateView):
    template_name = 'newsfeedner/wordclouds.html'


class AboutView(TemplateView):
    template_name = 'newsfeedner/about.html'


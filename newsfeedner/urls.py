from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import MainPage, WordClouds, EntityDetail, AboutView, EntityClassList


urlpatterns = [
    path('', MainPage.as_view(), name='main_page'),
    path('wordclouds/', WordClouds.as_view(), name='wordclouds'),
    path('about/', AboutView.as_view(), name='about'),
    path('entity-class/<ent_class>', EntityClassList.as_view(), name='ent_class'),
    path('entities/<entity>/', EntityDetail.as_view(), name='entity_detail'),
] + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)

from django.db import models
from django.contrib.postgres.fields import JSONField


URL_MAX_LENGTH = 2048  # https://stackoverflow.com/a/417184


class Feed(models.Model):
    name = models.CharField(verbose_name='feed_name', max_length=200)
    url = models.URLField(
        verbose_name='feed address',
        max_length=URL_MAX_LENGTH,
        unique=True,
    )
    last_fetched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Article(models.Model):
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
    id_in_feed = models.CharField(max_length=400)

    url = models.URLField(max_length=URL_MAX_LENGTH, blank=True, null=False)
    title = models.TextField(blank=True, null=False)
    title_json = JSONField(blank=True, null=True)
    published_parsed = models.DateTimeField(null=True, blank=True)

    article_entities = models.ManyToManyField('FeedEntities')
    is_entities_parsed = models.BooleanField(default=False)

    class Meta:
        ordering = ('-published_parsed',)

    def __str__(self):
        return "{}: {}".format(self.feed.name, self.title)


class Entity(models.Model):
    ENTITY_CLASSES = (
        ('PER', 'Person'),
        ('ORG', 'Organisation'),
        ('LOC', 'Location'),
    )
    name = models.CharField(max_length=100)
    name_translit = models.CharField(max_length=100)
    entity_class = models.CharField(max_length=3, choices=ENTITY_CLASSES)

    def __str__(self):
        return self.name


class FeedEntities(models.Model):
    ent = models.ForeignKey(Entity, on_delete=models.CASCADE)
    words = models.CharField(max_length=100)

    def __str__(self):
        return "{}: {}".format(self.words, self.ent.name)

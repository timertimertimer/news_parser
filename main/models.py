from django.db import models


class Article(models.Model):
    link = models.CharField(max_length=255, unique=True)
    source = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    date = models.IntegerField(null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    text = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return self.title

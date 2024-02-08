from apps.core.models import TimeStampedModel
from django.contrib.auth.models import User
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=24)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return f"{self.name}"


ARTICLE_TYPES = [
    ("UN", "Unspecified"),
    ("TU", "Tutorial"),
    ("RS", "Research"),
    ("RW", "Review"),
]

class Article(TimeStampedModel):
    title = models.CharField(max_length=256)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=3, choices=ARTICLE_TYPES, default="UN")
    categories = models.ManyToManyField(Category, blank=True, related_name="categories")
    content = models.TextField()

    def __str__(self):
        return f"{self.author}: {self.title} ({self.created_at.date()})"
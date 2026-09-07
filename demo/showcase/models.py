import uuid

from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=40, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Author(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    website = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    avatar = models.FileField(upload_to="avatars/", blank=True)
    joined = models.DateField()
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        REVIEW = "review", "In review"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="articles")
    author = models.ForeignKey(Author, on_delete=models.PROTECT, related_name="articles")
    tags = models.ManyToManyField(Tag, blank=True, related_name="articles")
    related_articles = models.ManyToManyField("self", blank=True)
    summary = models.CharField(max_length=300, blank=True, help_text="Shown in listings and social previews.")
    body = models.TextField(help_text="Markdown is supported.")
    publish_date = models.DateTimeField(null=True, blank=True)
    review_deadline = models.DateField(null=True, blank=True)
    reading_time = models.TimeField(null=True, blank=True, help_text="Estimated time to read.")
    word_count = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    allow_comments = models.BooleanField(
        null=True, blank=True, help_text="Leave unset to inherit the category default."
    )
    cover = models.FileField(upload_to="covers/", blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    views = models.PositiveIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-publish_date", "title"]

    def __str__(self):
        return self.title


class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="comments")
    name = models.CharField(max_length=80)
    email = models.EmailField()
    body = models.TextField()
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.name} on {self.article}"


class Revision(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="revisions")
    number = models.PositiveIntegerField()
    notes = models.TextField(blank=True)
    editor = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["number"]
        unique_together = [("article", "number")]

    def __str__(self):
        return f"Revision {self.number} of {self.article}"

from django.contrib import admin
from django.utils import timezone

from .models import Article, Author, Category, Comment, Revision, Tag


class WordCountFilter(admin.SimpleListFilter):
    title = "length"
    parameter_name = "length"

    def lookups(self, request, model_admin):
        return [("short", "Short (< 500 words)"), ("medium", "Medium"), ("long", "Long (> 2000 words)")]

    def queryset(self, request, queryset):
        if self.value() == "short":
            return queryset.filter(word_count__lt=500)
        if self.value() == "medium":
            return queryset.filter(word_count__gte=500, word_count__lte=2000)
        if self.value() == "long":
            return queryset.filter(word_count__gt=2000)
        return queryset


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1
    fields = ["name", "email", "body", "is_public"]


class RevisionInline(admin.StackedInline):
    model = Revision
    extra = 0
    fields = ["number", "editor", "notes"]
    autocomplete_fields = ["editor"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "article_count", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}

    @admin.display(description="Articles")
    def article_count(self, obj):
        return obj.articles.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "website", "joined", "is_verified"]
    list_filter = ["is_verified", "joined"]
    search_fields = ["name", "email"]
    date_hierarchy = "joined"


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "category", "author", "publish_date", "is_featured", "word_count", "views"]
    list_display_links = ["title"]
    list_editable = ["is_featured"]
    list_filter = ["status", "category", "is_featured", WordCountFilter, "publish_date", "tags"]
    search_fields = ["title", "summary", "body"]
    date_hierarchy = "publish_date"
    list_per_page = 15
    show_facets = admin.ShowFacets.ALWAYS
    prepopulated_fields = {"slug": ["title"]}
    autocomplete_fields = ["author"]
    raw_id_fields = ["related_articles"]
    filter_horizontal = ["tags"]
    radio_fields = {"status": admin.HORIZONTAL}
    readonly_fields = ["uuid", "views", "created_at", "updated_at"]
    save_on_top = True
    actions = ["publish", "archive"]
    inlines = [CommentInline, RevisionInline]
    fieldsets = [
        (None, {"fields": ["title", "slug", "status", ("category", "author"), "summary", "body"]}),
        (
            "Publishing",
            {
                "fields": [
                    ("publish_date", "review_deadline"),
                    "reading_time",
                    ("is_featured", "allow_comments"),
                    "cover",
                ],
                "description": "Control when and how the article appears on the site.",
            },
        ),
        ("Taxonomy", {"fields": ["tags", "related_articles"]}),
        (
            "Advanced",
            {
                "classes": ["collapse"],
                "fields": ["word_count", "rating", "metadata"],
            },
        ),
        ("Audit", {"classes": ["collapse"], "fields": ["uuid", "views", ("created_at", "updated_at")]}),
    ]

    @admin.action(description="Publish selected articles")
    def publish(self, request, queryset):
        updated = queryset.update(status=Article.Status.PUBLISHED, publish_date=timezone.now())
        self.message_user(request, f"{updated} article(s) published.")

    @admin.action(description="Archive selected articles")
    def archive(self, request, queryset):
        updated = queryset.update(status=Article.Status.ARCHIVED)
        self.message_user(request, f"{updated} article(s) archived.", level="warning")

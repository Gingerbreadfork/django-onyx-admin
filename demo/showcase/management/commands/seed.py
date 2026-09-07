import random
from datetime import time, timedelta
from decimal import Decimal

from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from demo.showcase.models import Article, Author, Category, Comment, Revision, Tag
from demo.store.models import Order, OrderItem, Product

WORDS = (
    "edge runtime cache deploy preview branch build serverless function domain "
    "latency region rollback observability incident postmortem migration schema "
    "index query replica throughput retry queue worker webhook signature token "
    "design system typography grid spacing contrast palette component layout "
    "roadmap launch pricing tier quota billing invoice customer support onboarding"
).split()

TITLES = [
    "Shipping faster with preview deployments",
    "How we cut cold starts by 40%",
    "A practical guide to edge caching",
    "Designing for dark mode from day one",
    "Postmortem: the March routing incident",
    "Rethinking our billing pipeline",
    "What we learned migrating to a monorepo",
    "Typography that scales across products",
    "Zero-downtime schema migrations",
    "Observability on a budget",
    "Why we moved our queue to Postgres",
    "Onboarding that actually converts",
    "Introducing regional failover",
    "The case for boring infrastructure",
    "Measuring latency where users are",
    "Building a design system people use",
]

PRODUCTS = [
    ("Hobby plan", "PLAN-HOBBY", "0.00"),
    ("Pro plan", "PLAN-PRO", "20.00"),
    ("Enterprise plan", "PLAN-ENT", "250.00"),
    ("Extra bandwidth (100 GB)", "ADD-BW-100", "40.00"),
    ("Extra seats (5)", "ADD-SEATS-5", "50.00"),
    ("Edge config", "ADD-EDGECFG", "3.00"),
    ("Analytics", "ADD-ANALYTICS", "10.00"),
    ("Speed insights", "ADD-SPEED", "10.00"),
    ("Image optimization (1k)", "ADD-IMG-1K", "5.00"),
    ("Log drains", "ADD-LOGS", "15.00"),
    ("Monitoring", "ADD-MON", "10.00"),
    ("Password protection", "ADD-PWP", "150.00"),
    ("Preview comments", "ADD-COMMENTS", "0.00"),
    ("Web application firewall", "ADD-WAF", "20.00"),
    ("Custom domains (10)", "ADD-DOM-10", "0.00"),
    ("Serverless functions (1M)", "ADD-FN-1M", "0.60"),
    ("KV storage", "ADD-KV", "1.00"),
    ("Postgres (compute hours)", "ADD-PG", "0.10"),
    ("Blob storage (GB)", "ADD-BLOB", "0.03"),
    ("Cron jobs", "ADD-CRON", "0.00"),
]

PEOPLE = [
    ("Ada Lovelace", "ada@example.com"),
    ("Grace Hopper", "grace@example.com"),
    ("Linus Torvalds", "linus@example.com"),
    ("Margaret Hamilton", "margaret@example.com"),
    ("Dennis Ritchie", "dennis@example.com"),
    ("Barbara Liskov", "barbara@example.com"),
    ("Ken Thompson", "ken@example.com"),
    ("Radia Perlman", "radia@example.com"),
]


def words(rng, n):
    return " ".join(rng.choice(WORDS) for _ in range(n))


def sentence(rng):
    return words(rng, rng.randint(8, 16)).capitalize() + "."


def paragraph(rng, sentences=4):
    return " ".join(sentence(rng) for _ in range(sentences))


class Command(BaseCommand):
    help = "Create a superuser (admin / admin) and sample data for the demo admin."

    def handle(self, *args, **options):
        User = get_user_model()
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com", "is_staff": True, "is_superuser": True},
        )
        if created:
            admin.set_password("admin")
            admin.save()
            self.stdout.write("Created superuser admin / admin")

        for username in ("grace", "ada"):
            staff, created = User.objects.get_or_create(
                username=username, defaults={"email": f"{username}@example.com", "is_staff": True, "is_superuser": True}
            )
            if created:
                staff.set_password("admin")
                staff.save()

        if Article.objects.exists():
            self.seed_activity()
            self.stdout.write("Sample data already present.")
            return

        rng = random.Random(42)
        now = timezone.now()

        categories = [
            Category.objects.create(
                name=name, slug=slugify(name), description=sentence(rng), is_active=name != "Archive"
            )
            for name in ["Engineering", "Design", "Product", "Company", "Changelog", "Community", "Archive"]
        ]
        tags = [
            Tag.objects.create(name=name)
            for name in [
                "edge",
                "caching",
                "postgres",
                "typescript",
                "design",
                "incident",
                "billing",
                "dx",
                "performance",
                "security",
                "launch",
                "hiring",
            ]
        ]
        authors = [
            Author.objects.create(
                name=name,
                email=email,
                website=f"https://{email.split('@')[0]}.example.com" if i % 2 == 0 else "",
                bio=paragraph(rng, 2),
                joined=(now - timedelta(days=rng.randint(30, 1500))).date(),
                is_verified=i % 3 != 0,
            )
            for i, (name, email) in enumerate(PEOPLE[:6])
        ]

        statuses = (
            [Article.Status.PUBLISHED] * 5
            + [Article.Status.DRAFT] * 2
            + [Article.Status.REVIEW, Article.Status.ARCHIVED]
        )
        articles = []
        for i in range(48):
            title = (
                TITLES[i % len(TITLES)] if i < len(TITLES) else f"{TITLES[i % len(TITLES)]} ({i // len(TITLES) + 1})"
            )
            status = rng.choice(statuses)
            published = status in (Article.Status.PUBLISHED, Article.Status.ARCHIVED)
            article = Article.objects.create(
                title=title,
                slug=slugify(title),
                status=status,
                category=rng.choice(categories[:6]),
                author=rng.choice(authors),
                summary=sentence(rng),
                body="\n\n".join(paragraph(rng) for _ in range(rng.randint(2, 5))),
                publish_date=now - timedelta(days=rng.randint(0, 400), hours=rng.randint(0, 23)) if published else None,
                review_deadline=(now + timedelta(days=rng.randint(1, 30))).date()
                if status == Article.Status.REVIEW
                else None,
                reading_time=time(0, rng.randint(2, 14)),
                word_count=rng.choice([320, 480, 900, 1400, 2100, 3200]),
                rating=Decimal(rng.randint(25, 50)) / 10 if published else None,
                is_featured=rng.random() < 0.2,
                allow_comments=rng.choice([True, False, None]),
                metadata={"reviewers": rng.randint(1, 3), "canonical": f"https://example.com/blog/{slugify(title)}"},
                views=rng.randint(0, 25000) if published else 0,
            )
            article.tags.set(rng.sample(tags, rng.randint(1, 3)))
            articles.append(article)

        for article in articles:
            for _ in range(rng.randint(0, 3)):
                name, email = rng.choice(PEOPLE)
                Comment.objects.create(
                    article=article, name=name, email=email, body=paragraph(rng, 2), is_public=rng.random() > 0.2
                )
            for number in range(1, rng.randint(1, 3)):
                Revision.objects.create(article=article, number=number, notes=sentence(rng), editor=rng.choice(authors))
            if rng.random() < 0.3:
                article.related_articles.set(rng.sample(articles, 2))

        products = [
            Product.objects.create(
                name=name,
                sku=sku,
                price=Decimal(price),
                stock=rng.randint(0, 500),
                is_available=rng.random() > 0.15,
                description=sentence(rng),
            )
            for name, sku, price in PRODUCTS
        ]
        order_statuses = (
            [Order.Status.PAID] * 4 + [Order.Status.SHIPPED] * 3 + [Order.Status.PENDING, Order.Status.CANCELLED]
        )
        for i in range(36):
            name, email = rng.choice(PEOPLE)
            order = Order.objects.create(
                reference=f"ORD-{10240 + i}",
                customer_name=name,
                customer_email=email,
                status=rng.choice(order_statuses),
                notes=sentence(rng) if rng.random() < 0.3 else "",
                placed_at=now - timedelta(days=rng.randint(0, 120), hours=rng.randint(0, 23)),
            )
            total = Decimal("0")
            for product in rng.sample(products, rng.randint(1, 4)):
                quantity = rng.randint(1, 5)
                OrderItem.objects.create(order=order, product=product, quantity=quantity, unit_price=product.price)
                total += product.price * quantity
            order.total = total
            order.save(update_fields=["total"])

        LogEntry.objects.log_actions(admin.pk, articles[:3], ADDITION, "Added.")
        LogEntry.objects.log_actions(admin.pk, articles[3:6], CHANGE, [{"changed": {"fields": ["Status"]}}])
        LogEntry.objects.log_actions(admin.pk, products[:2], CHANGE, [{"changed": {"fields": ["Price", "Stock"]}}])

        self.seed_activity()
        self.stdout.write(self.style.SUCCESS("Seeded demo data."))

    def seed_activity(self):
        if LogEntry.objects.count() >= 60:
            return
        rng = random.Random(7)
        now = timezone.now()
        User = get_user_model()
        users = list(User.objects.filter(is_staff=True))
        targets = list(Article.objects.all()[:30]) + list(Product.objects.all()[:10]) + list(Order.objects.all()[:10])
        flags = [ADDITION] * 3 + [CHANGE] * 7 + [DELETION]
        for _ in range(160):
            obj = rng.choice(targets)
            flag = rng.choice(flags)
            age = rng.triangular(0, 14, 1)
            LogEntry.objects.create(
                action_time=now - timedelta(days=age, minutes=rng.randint(0, 600)),
                user=rng.choice(users),
                content_type=ContentType.objects.get_for_model(obj),
                object_id=obj.pk,
                object_repr=str(obj)[:200],
                action_flag=flag,
                change_message="Added."
                if flag == ADDITION
                else ('[{"changed": {"fields": ["Status"]}}]' if flag == CHANGE else ""),
            )

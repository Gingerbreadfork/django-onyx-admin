import pytest
from django.utils import timezone

from demo.showcase.models import Article, Author, Category, Tag
from demo.store.models import Order, Product


@pytest.fixture
def sample_data(db):
    category = Category.objects.create(name="Engineering", slug="engineering")
    author = Author.objects.create(name="Ada Lovelace", email="ada@example.com", joined=timezone.now().date())
    tag = Tag.objects.create(name="edge")
    article = Article.objects.create(
        title="Hello world",
        slug="hello-world",
        category=category,
        author=author,
        body="Body",
        publish_date=timezone.now(),
    )
    article.tags.add(tag)
    product = Product.objects.create(name="Pro plan", sku="PLAN-PRO", price="20.00")
    order = Order.objects.create(
        reference="ORD-1",
        customer_name="Ada",
        customer_email="ada@example.com",
        placed_at=timezone.now(),
    )
    return {"article": article, "author": author, "category": category, "product": product, "order": order}

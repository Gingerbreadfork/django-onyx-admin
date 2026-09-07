import django
import pytest
from django.contrib.staticfiles import finders
from django.template import Context, Template
from django.test import RequestFactory
from django.urls import reverse

THEME_CSS = "onyx_admin/css/onyx.css"


def page_urls(data):
    article = data["article"]
    return [
        reverse("admin:index"),
        reverse("admin:app_list", kwargs={"app_label": "showcase"}),
        reverse("admin:showcase_article_changelist"),
        reverse("admin:showcase_article_changelist") + "?q=hello&status__exact=draft&_facets",
        reverse("admin:showcase_article_add"),
        reverse("admin:showcase_article_change", args=[article.pk]),
        reverse("admin:showcase_article_delete", args=[article.pk]),
        reverse("admin:showcase_article_history", args=[article.pk]),
        reverse("admin:showcase_author_changelist"),
        reverse("admin:store_product_changelist"),
        reverse("admin:store_order_change", args=[data["order"].pk]),
        reverse("admin:auth_user_changelist"),
        reverse("admin:auth_user_add"),
        reverse("admin:password_change"),
    ]


@pytest.mark.django_db
def test_admin_pages_render_with_theme(admin_client, sample_data):
    for url in page_urls(sample_data):
        response = admin_client.get(url)
        assert response.status_code == 200, url
        html = response.content.decode()
        assert THEME_CSS in html, url
        assert html.index("admin/css/responsive.css") < html.index(THEME_CSS), url


@pytest.mark.django_db
def test_login_page_uses_theme(client):
    response = client.get(reverse("admin:login"))
    assert response.status_code == 200
    html = response.content.decode()
    assert THEME_CSS in html
    assert 'class="theme-toggle"' in html


@pytest.mark.django_db
def test_popup_pages_use_theme(admin_client, sample_data):
    response = admin_client.get(reverse("admin:showcase_category_add") + "?_popup=1")
    assert response.status_code == 200
    assert THEME_CSS in response.content.decode()


@pytest.mark.django_db
def test_changelist_actions_and_editable_rows(admin_client, sample_data):
    url = reverse("admin:store_product_changelist")
    response = admin_client.get(url)
    html = response.content.decode()
    assert 'class="actions"' in html
    assert 'name="form-0-price"' in html


def test_nonce_attr_rendered_when_request_has_nonce():
    request = RequestFactory().get("/")
    request.csp_nonce = "abc123"
    rendered = Template("{% load onyx_admin %}<link{% onyx_nonce_attr %}>").render(Context({"request": request}))
    assert rendered == '<link nonce="abc123">'


def test_nonce_attr_is_empty_without_nonce():
    request = RequestFactory().get("/")
    template = Template("{% load onyx_admin %}<link{% onyx_nonce_attr %}>")
    assert template.render(Context({"request": request})) == "<link>"
    assert template.render(Context({})) == "<link>"


def test_static_assets_are_discoverable():
    for path in [THEME_CSS, "onyx_admin/fonts/geist-sans.woff2", "onyx_admin/fonts/geist-mono.woff2"]:
        assert finders.find(path), path


def test_supported_django_version():
    assert django.VERSION >= (5, 2)


@pytest.mark.django_db
def test_dashboard_has_sidebar_tiles_and_palette(admin_client):
    html = admin_client.get(reverse("admin:index")).content.decode()
    assert 'id="nav-sidebar"' in html
    assert 'class="onyx-app-icon onyx-hue-' in html
    assert 'class="onyx-palette-trigger"' in html
    assert 'class="onyx-avatar onyx-hue-' in html
    assert 'class="onyx-greeting"' in html
    assert "onyx_admin/js/onyx.js" in html


def test_hue_filter_is_stable_and_bounded():
    from onyx_admin.templatetags.onyx_admin import onyx_hue

    assert onyx_hue("showcase") == onyx_hue("showcase")
    assert onyx_hue("showcase") != onyx_hue("store")
    assert all(0 <= int(onyx_hue(str(n)).rsplit("-", 1)[1]) < 12 for n in range(50))


@pytest.mark.django_db
def test_dashboard_activity_overview(admin_client, admin_user, sample_data):
    from django.contrib.admin.models import ADDITION, CHANGE, LogEntry

    article = sample_data["article"]
    LogEntry.objects.log_actions(admin_user.pk, [article], ADDITION, "Added.")
    LogEntry.objects.log_actions(admin_user.pk, [article], CHANGE, [{"changed": {"fields": ["Title"]}}])
    html = admin_client.get(reverse("admin:index")).content.decode()
    assert 'class="onyx-overview"' in html
    assert 'class="onyx-bar onyx-bar-add"' in html
    assert 'class="onyx-bar onyx-bar-change"' in html
    assert reverse("admin:showcase_article_change", args=[article.pk]) in html


@pytest.mark.django_db
def test_dashboard_activity_hidden_without_entries_or_when_disabled(admin_client, admin_user, sample_data, settings):
    from django.contrib.admin.models import ADDITION, LogEntry

    assert 'class="onyx-overview"' not in admin_client.get(reverse("admin:index")).content.decode()
    LogEntry.objects.log_actions(admin_user.pk, [sample_data["article"]], ADDITION, "Added.")
    settings.ONYX_DASHBOARD_ACTIVITY = False
    assert 'class="onyx-overview"' not in admin_client.get(reverse("admin:index")).content.decode()


@pytest.mark.django_db
def test_dashboard_activity_respects_permissions(client, django_user_model, admin_user, sample_data):
    from django.contrib.admin.models import ADDITION, LogEntry
    from django.contrib.auth.models import Permission

    LogEntry.objects.log_actions(admin_user.pk, [sample_data["article"]], ADDITION, "Added.")
    staff = django_user_model.objects.create_user("viewer", password="x", is_staff=True)
    staff.user_permissions.add(Permission.objects.get(codename="view_product"))
    client.force_login(staff)
    html = client.get(reverse("admin:index")).content.decode()
    assert 'class="onyx-overview"' not in html
    staff.user_permissions.add(Permission.objects.get(codename="view_article"))
    html = client.get(reverse("admin:index")).content.decode()
    assert 'class="onyx-overview"' in html
    assert "Hello world" in html


@pytest.mark.django_db
def test_sidebar_renders_recent_script_and_visible_palette_trigger(admin_client):
    html = admin_client.get(reverse("admin:showcase_article_changelist")).content.decode()
    assert "onyx_admin/js/sidebar.js" in html
    assert 'class="onyx-palette-trigger" data-placeholder="Search">' in html
    assert finders.find("onyx_admin/js/sidebar.js")


@pytest.mark.django_db
def test_phone_drawer_toggle_only_for_signed_in_users(admin_client, client):
    assert 'class="onyx-menu-toggle"' in admin_client.get(reverse("admin:index")).content.decode()
    assert 'class="onyx-menu-toggle"' not in client.get(reverse("admin:login")).content.decode()


@pytest.mark.django_db
def test_font_setting_controls_body_class_and_preload(admin_client, settings):
    html = admin_client.get(reverse("admin:index")).content.decode()
    assert "onyx-font-inter" in html
    assert "onyx_admin/fonts/inter/inter-latin.woff2" in html
    settings.ONYX_FONT = "geist"
    html = admin_client.get(reverse("admin:index")).content.decode()
    assert "onyx-font-geist" in html
    assert "onyx_admin/fonts/geist-sans.woff2" in html
    settings.ONYX_FONT = "nonsense"
    assert "onyx-font-inter" in admin_client.get(reverse("admin:index")).content.decode()
    assert finders.find("onyx_admin/fonts/inter/inter-latin.woff2")


@pytest.mark.django_db
def test_login_and_logged_out_pages_use_polished_markup(client, admin_client):
    html = client.get(reverse("admin:login")).content.decode()
    assert "onyx-login-subtitle" not in html
    assert 'class="onyx-password-toggle"' in html
    assert 'class="onyx-capslock"' in html
    assert 'name="next"' in html
    response = client.post(reverse("admin:login"), {"username": "nobody", "password": "wrong"})
    assert response.status_code == 200
    assert 'class="errornote"' in response.content.decode()
    response = admin_client.post(reverse("admin:logout"))
    assert response.status_code == 200
    html = response.content.decode()
    assert "onyx-logged-out" in html
    assert 'class="button default"' in html


@pytest.mark.django_db
def test_collectstatic_with_manifest_storage(tmp_path, settings):
    from django.core.management import call_command

    settings.STATIC_ROOT = tmp_path
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
    }
    call_command("collectstatic", interactive=False, verbosity=0)
    manifest = (tmp_path / "staticfiles.json").read_text()
    assert "onyx_admin/css/onyx.css" in manifest
    assert "onyx_admin/fonts/inter/inter-latin.woff2" in manifest
    hashed_css = next(tmp_path.glob("onyx_admin/css/onyx.*.css"))
    assert "inter-latin." in hashed_css.read_text()

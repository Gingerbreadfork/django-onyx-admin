import zlib
from datetime import timedelta

from django import template
from django.conf import settings
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.html import format_html

register = template.Library()

FLAGS = {ADDITION: "add", CHANGE: "change", DELETION: "delete"}
CHART_DAYS = 14
CHART_HEIGHT = 60
BAR_STEP = 20
BAR_WIDTH = 14


@register.simple_tag(takes_context=True)
def onyx_nonce_attr(context):
    """Render a nonce attribute when the request carries a CSP nonce."""
    request = context.get("request")
    nonce = getattr(request, "csp_nonce", None) if request is not None else None
    if not nonce:
        return ""
    return format_html(' nonce="{}"', nonce)


FONTS = ("inter", "geist", "system")


@register.simple_tag
def onyx_font():
    """Name of the UI font family chosen with ONYX_FONT."""
    font = str(getattr(settings, "ONYX_FONT", "inter")).lower()
    return font if font in FONTS else "inter"


@register.filter
def onyx_hue(value):
    """Map any string to one of twelve stable colour classes."""
    return f"onyx-hue-{zlib.crc32(str(value).encode('utf-8')) % 12}"


def _can_see(user, content_type):
    if content_type is None or user.is_superuser:
        return True
    label, model = content_type.app_label, content_type.model
    return user.has_perm(f"{label}.view_{model}") or user.has_perm(f"{label}.change_{model}")


def _object_url(content_type, entry):
    if content_type is None or entry.action_flag == DELETION or not entry.object_id:
        return None
    try:
        return reverse(f"admin:{content_type.app_label}_{content_type.model}_change", args=(entry.object_id,))
    except NoReverseMatch:
        return None


@register.simple_tag(takes_context=True)
def onyx_activity(context, limit=400):
    """Summarise recent admin log entries the current user is allowed to see."""
    if not getattr(settings, "ONYX_DASHBOARD_ACTIVITY", True):
        return None
    request = context.get("request")
    user = getattr(request, "user", None)
    if user is None or not user.is_active or not user.is_staff:
        return None

    now = timezone.now()
    today = timezone.localdate() if settings.USE_TZ else now.date()
    week_ago = now - timedelta(days=7)
    days = [today - timedelta(days=offset) for offset in range(CHART_DAYS - 1, -1, -1)]
    buckets = {day: {"add": 0, "change": 0, "delete": 0} for day in days}
    stats = {"add": 0, "change": 0, "delete": 0}
    active_users = set()
    feed = []
    seen = 0

    entries = LogEntry.objects.select_related("user").order_by("-pk")[:limit]
    for entry in entries:
        content_type = ContentType.objects.get_for_id(entry.content_type_id) if entry.content_type_id else None
        kind = FLAGS.get(entry.action_flag)
        if kind is None or not _can_see(user, content_type):
            continue
        seen += 1
        when = entry.action_time
        if timezone.is_aware(when):
            when = timezone.localtime(when)
        if when.date() in buckets:
            buckets[when.date()][kind] += 1
        if entry.action_time >= week_ago:
            stats[kind] += 1
            active_users.add(entry.user_id)
        if len(feed) < 8:
            feed.append(
                {
                    "username": entry.user.get_username(),
                    "kind": kind,
                    "model": content_type.name if content_type is not None else "",
                    "repr": entry.object_repr,
                    "url": _object_url(content_type, entry),
                    "time": entry.action_time,
                }
            )

    if not seen:
        return None

    peak = max(sum(bucket.values()) for bucket in buckets.values()) or 1
    chart = []
    for index, day in enumerate(days):
        bucket = buckets[day]
        segments = []
        cursor = CHART_HEIGHT + 2
        for kind in ("add", "change", "delete"):
            height = round(bucket[kind] / peak * CHART_HEIGHT, 1)
            if height:
                cursor -= height
                segments.append({"kind": kind, "y": cursor, "height": height})
        chart.append(
            {
                "day": day,
                "x": index * BAR_STEP + (BAR_STEP - BAR_WIDTH) / 2,
                "segments": segments,
                "total": sum(bucket.values()),
                **bucket,
            }
        )

    return {
        "stats": stats,
        "active_users": len(active_users),
        "chart": chart,
        "chart_width": CHART_DAYS * BAR_STEP,
        "chart_height": CHART_HEIGHT + 4,
        "bar_width": BAR_WIDTH,
        "feed": feed,
        "first_day": days[0],
    }

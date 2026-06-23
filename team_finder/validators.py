from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_github_url(url):
    if not url:
        return

    host = urlparse(url).netloc.lower().removeprefix("www.")
    if host != "github.com" and not host.endswith(".github.com"):
        raise ValidationError(_("Ссылка должна вести на GitHub."))

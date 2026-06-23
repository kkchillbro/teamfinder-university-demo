from django.core.paginator import Paginator

from .constants import ITEMS_PER_PAGE


def get_page_obj(queryset, page_number, per_page=ITEMS_PER_PAGE):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(page_number)

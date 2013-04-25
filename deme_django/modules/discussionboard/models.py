from django.db import models
from cms.models import Item
from django.utils.translation import ugettext_lazy as _

__all__ = ['DiscussionBoard']

class DiscussionBoard(Item):

    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create DiscussionBoard'])
    dyadic_relations = {}

    class Meta:
        verbose_name = _('discussion board')
        verbose_name_plural = _('discussion boards')

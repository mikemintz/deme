from django.db import models
from cms.models import Person
from django.utils.translation import ugettext_lazy as _

__all__ = ['CommunityForumParticipant'] 

class CommunityForumParticipant(Person):

    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view CommunityForumParticipant.webex_id', 'edit CommunityForumParticipant.webex_id'])
    introduced_global_abilities = frozenset(['create CommunityForumParticipant'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('community forum participant')
        verbose_name_plural = _('community forum participants')

    # Fields
    webex_id = models.CharField(_('webex id'), max_length=255) 


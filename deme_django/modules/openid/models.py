from cms.models import *
from django.db import models
from django.utils.translation import ugettext_lazy as _

__all__ = ['OpenidAccount']

class OpenidAccount(AuthenticationMethod):
    """
    This is an AuthenticationMethod that allows a user to log on with an
    OpenID.
    
    The openid url must be unique across the entire Deme installation.
    """

    # Setup
    introduced_immutable_fields = frozenset(['openid_url'])
    introduced_abilities = frozenset(['view OpenidAccount.openid_url'])
    introduced_global_abilities = frozenset(['create OpenidAccount'])
    class Meta:
        verbose_name = _('OpenID account')
        verbose_name_plural = _('OpenID accounts')

    # Fields
    openid_url = models.CharField(_('OpenID URL'), max_length=2047, unique=True)


from cms.models import *
from django.db import models
from django.utils.translation import ugettext_lazy as _

__all__ = ['WebauthAccount']

class WebauthAccount(AuthenticationMethod):
    """
    This is an AuthenticationMethod that allows a user to log on with
    Stanford's WebAuth system.
    
    The username must be unique across the entire Deme installation.
    """

    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view WebauthAccount.username', 'edit WebauthAccount.username'])
    introduced_global_abilities = frozenset(['create WebauthAccount'])
    class Meta:
        verbose_name = _('WebAuth account')
        verbose_name_plural = _('WebAuth accounts')

    # Fields
    username = models.CharField(_('username'), max_length=255, unique=True)


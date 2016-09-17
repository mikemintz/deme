from cms.models import AuthenticationMethod
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.http import int_to_base36, base36_to_int
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils import six
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import hashlib
import random
from django import forms
from django.utils.http import int_to_base36

__all__ = ['DemeAccount']

class DemeAccount(AuthenticationMethod):
    """
    This is an AuthenticationMethod that allows a user to log on with a
    username and a password.

    The username must be unique across the entire Deme installation. The
    password field is formatted the same as in the User model of the Django
    admin app (algo$salt$hash), and is thus not stored in plain text.
    """

    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset([
        'view DemeAccount.username', 'edit DemeAccount.username',
        'view DemeAccount.password', 'edit DemeAccount.password',
        'view DemeAccount.password_question', 'edit DemeAccount.password_question',
        'view DemeAccount.password_answer', 'edit DemeAccount.password_answer',
        'view DemeAccount.last_login',
    ])
    introduced_global_abilities = frozenset(['create DemeAccount'])
    dyadic_relations = {}
    class Meta:
        verbose_name = _('Deme account')
        verbose_name_plural = _('Deme accounts')

    # Fields
    username          = models.CharField(_('username'), max_length=255, unique=True)
    password          = models.CharField(_('password'), max_length=128)
    password_question = models.CharField(_('password question'), max_length=255, blank=True)
    password_answer   = models.CharField(_('password answer'), max_length=255, blank=True)
    last_login        = models.DateTimeField(_('last login'), blank=True, null=True)

    def set_password(self, raw_password):
        """
        Set the password field by generating a salt and hashing the raw
        password. This method does not make any database writes.
        """
        algo = 'sha1'
        salt = DemeAccount.get_random_hash()[:5]
        hsh = DemeAccount.get_hexdigest(algo, salt, raw_password)
        self.password = '%s$%s$%s' % (algo, salt, hsh)
    set_password.alters_data = True

    def check_password(self, raw_password):
        """
        Returns a boolean of whether the raw_password was correct. Handles
        encryption formats behind the scenes.
        """
        algo, salt, hsh = self.password.split('$')
        return hsh == DemeAccount.get_hexdigest(algo, salt, raw_password)

    def check_nonced_password(self, hashed_password, nonce):
        """
        Return True if the specified nonced password matches the password field.

        This method is here to allow a browser to login over an insecure
        connection. The browser is given the algorithm, the salt, and a random
        nonce, and is supposed to generate the following string, which this
        method generates and compares against:

            sha1(nonce, algo(salt, raw_password))
        """
        algo, salt, hsh = self.password.split('$')
        return DemeAccount.get_hexdigest('sha1', nonce, hsh) == hashed_password

    def make_uid(self):
        return int_to_base36(self.pk)

    def make_token(self):
        generator = PasswordResetTokenGenerator()
        return generator.make_token(self)

    def check_token(self, token):
        generator = PasswordResetTokenGenerator()
        return generator.check_token(self, token)

    @staticmethod
    def mysql_pre41_password(raw_password):
        """
        Encrypt a password using the same algorithm MySQL used for PASSWORD()
        prior to 4.1.

        This method is here to support migrations of account/password data
        from websites that encrypted passwords this way.
        """
        # ported to python from http://packages.debian.org/lenny/libcrypt-mysql-perl
        nr = 1345345333L
        add = 7
        nr2 = 0x12345671L
        for ch in raw_password:
            if ch == ' ' or ch == '\t':
                continue # skip spaces in raw_password
            tmp = ord(ch)
            nr ^= (((nr & 63) + add) * tmp) + (nr << 8)
            nr2 += (nr2 << 8) ^ nr
            add += tmp
        result1 = nr & ((1L << 31) - 1L) # Don't use sign bit (str2int)
        result2 = nr2 & ((1L << 31) - 1L)
        return "%08lx%08lx" % (result1, result2)

    @staticmethod
    def get_hexdigest(algorithm, salt, raw_password):
        """
        Return a string of the hexdigest of the given plaintext password and salt
        using the given algorithm ('sha1' or 'mysql_pre41_password').
        """
        from django.utils.encoding import smart_str
        raw_password, salt = smart_str(raw_password), smart_str(salt)
        if algorithm == 'sha1':
            return hashlib.sha1(salt + raw_password).hexdigest()
        elif algorithm == 'mysql_pre41_password':
            return DemeAccount.mysql_pre41_password(raw_password)
        raise ValueError("Got unknown password algorithm type in password.")

    @staticmethod
    def get_random_hash():
        """Return a random 40-digit hexadecimal string. """
        return DemeAccount.get_hexdigest('sha1', str(random.random()), str(random.random()))

    @classmethod
    def do_specialized_form_configuration(cls, item_type, is_new, attrs):
        super(DemeAccount, cls).do_specialized_form_configuration(item_type, is_new, attrs)
        attrs['Meta'].exclude.append('password')
        attrs['password1'] = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
        attrs['password2'] = forms.CharField(label=_("Password confirmation"), widget=forms.PasswordInput)
        def clean_password2(self):
            password1 = self.cleaned_data.get("password1", "")
            password2 = self.cleaned_data["password2"]
            if password1 != password2:
                raise forms.ValidationError(_("The two password fields didn't match."))
            return password2
        def save(self, commit=True):
            item = super(forms.models.ModelForm, self).save(commit=False)
            item.set_password(self.cleaned_data["password1"])
            if commit:
                item.save()
            return item
        attrs['clean_password2'] = clean_password2
        attrs['save'] = save


from cms.models import AuthenticationMethod
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.http import int_to_base36, base36_to_int
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils import six
import hashlib
import random
from django import forms

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
    introduced_abilities = frozenset(['view DemeAccount.username', 'view DemeAccount.password',
                                      'view DemeAccount.password_question', 'view DemeAccount.password_answer',
                                      'edit DemeAccount.username', 'edit DemeAccount.password',
                                      'edit DemeAccount.password_question', 'edit DemeAccount.password_answer'])
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

    def make_token(self):
        """
        Returns a token that can be used once to do a password reset
        for the given account. Based on the default Django token generator
        """
        return self._make_token_with_timestamp(self._num_days(self._today()))

    def check_token(self, token):
        """
        Check that a password reset token is correct for a given user.
        """
        # Parse the token
        try:
            ts_b36, hash = token.split("-")
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        if not constant_time_compare(self._make_token_with_timestamp(ts), token):
            return False

        # Check the timestamp is within limit
        if (self._num_days(self._today()) - ts) > settings.PASSWORD_RESET_TIMEOUT_DAYS:
            return False

        return True

    def _make_token_with_timestamp(self, timestamp):
        # timestamp is number of days since 2001-1-1.  Converted to
        # base 36, this gives us a 3 digit string until about 2121
        ts_b36 = int_to_base36(timestamp)

        # By hashing on the internal state of the user and using state
        # that is sure to change (the password salt will change as soon as
        # the password is set, at least for current Django auth, and
        # last_login will also change), we produce a hash that will be
        # invalid as soon as it is used.
        # We limit the hash to 20 chars to keep URL short
        key_salt = "deme_django.modules.demeaccount.models.DemeAccount"

        # Ensure results are consistent across DB backends
        # TODO: integrate login_timestamp if we ever track this field
        # login_timestamp = user.last_login.replace(microsecond=0, tzinfo=None)

        value = (six.text_type(self.pk) + self.password + six.text_type(timestamp))
        hash = salted_hmac(key_salt, value).hexdigest()[::2]
        return "%s-%s" % (ts_b36, hash)

    def _num_days(self, dt):
        return (dt - date(2001, 1, 1)).days

    def _today(self):
        # Used for mocking in tests
        return date.today()

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


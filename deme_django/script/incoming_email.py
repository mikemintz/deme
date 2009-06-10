#!/usr/bin/env python

# Set up the Django Enviroment
from django.core.management import setup_environ
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from deme_django import settings
setup_environ(settings)

from cms.models import *
from cms.permissions import MultiAgentPermissionCache
import email
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist

#TODO attachments? handle html formatting?
#TODO let people comment on specific versions, like 123.2@deme.stanford.edu

class UserException(Exception):
    def __init__(self, msg):
        super(UserException, self).__init__(msg)

def get_subject(msg):
    return msg['Subject'].replace('\n', '').replace('\t', '')

def get_from_email(msg):
    return email.utils.parseaddr(msg['From'])[1]

def handle_email(msg, item_id):
    multi_agent_permission_cache = MultiAgentPermissionCache()
    subject = get_subject(msg)
    if msg.is_multipart():
        body = msg.get_payload(0).get_payload()
    else:
        body = msg.get_payload()
    from_email = get_from_email(msg)
    to_email = "%s@%s" % (item_id, settings.NOTIFICATION_EMAIL_HOSTNAME)
    try:
        email_contact_method = EmailContactMethod.objects.get(email=from_email)
    except ObjectDoesNotExist:
        raise UserException('Error: Your comment could not be created because there is no agent with email address %s' % from_email)
    try:
        item = Item.objects.get(pk=item_id)
    except ObjectDoesNotExist:
        raise UserException('Error: Your comment could not be created because there does is no item %s' % item_id)
    permission_cache = multi_agent_permission_cache.get(email_contact_method.agent)
    if not permission_cache.agent_can('comment_on', item):
        raise UserException('Error: Your comment could not be created because you do not have permission to comment on the item %s' % item_id)

    agent = email_contact_method.agent

    #TODO permissions to view Item.name: technically you could figure out the name of an item by commenting on it here (same issue in cms/views.py)
    if issubclass(item.actual_item_type(), Comment):
        comment_name = item.display_name()
        if not comment_name.lower().startswith('re: '):
            comment_name = 'Re: %s' % comment_name
    else:
        comment_name = subject
    
    comment = TextComment(item=item, item_version_number=item.version_number, name=comment_name, body=body, from_contact_method=email_contact_method)
    comment.name = comment_name #TODO this is a hack due to multiple inheritance bug in Django. remove it when bug is fixed
    permissions = [OneToOnePermission(source=agent, ability='do_anything', is_allowed=True)]
    comment.save_versioned(action_agent=agent, initial_permissions=permissions)

def main():
    assert len(sys.argv) == 2
    item_id = sys.argv[1] # I.e., the mailbox
    msg = email.message_from_file(sys.stdin)
    try:
        handle_email(msg, item_id)
    except UserException, e:
        new_subject = 'Re: %s' % get_subject(msg)
        new_body = e.message
        our_email = "%s@%s" % (item_id, settings.NOTIFICATION_EMAIL_HOSTNAME)
        their_email = get_from_email(msg)
        send_mail(new_subject, new_body, our_email, [their_email])

if __name__ == '__main__':
    main()

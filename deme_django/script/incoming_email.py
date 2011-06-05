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
import time

#TODO attachments? handle html formatting?
#TODO let people comment on specific versions, like 123.2@deme.stanford.edu

class UserException(Exception):
    def __init__(self, msg):
        super(UserException, self).__init__(msg)

def get_subject(msg):
    return msg['Subject'].replace('\n', '').replace('\t', '')

def get_from_email(msg):
    return email.utils.parseaddr(msg['From'])[1]

def handle_email(msg, email_username):
    multi_agent_permission_cache = MultiAgentPermissionCache()
    subject = get_subject(msg)
    if msg.is_multipart():
        body = msg.get_payload(0).get_payload()
    else:
        body = msg.get_payload()
    from_email = get_from_email(msg)
    try:
        email_contact_method = EmailContactMethod.objects.get(email=from_email)
    except ObjectDoesNotExist:
        raise UserException('Error: Your comment could not be created because there is no agent with email address %s' % from_email)
    try:
        item = Item.item_for_notification_email_username(email_username)
    except ObjectDoesNotExist:
        raise UserException('Error: Your comment could not be created because there does is no item for email account %s' % email_username)
    permission_cache = multi_agent_permission_cache.get(email_contact_method.agent)
    if not permission_cache.agent_can('comment_on', item):
        display_name = item.display_name(permission_cache.agent_can('view Item.name', item))
        raise UserException('Error: Your comment could not be created because you do not have permission to comment on %s' % display_name)

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
    email_username = sys.argv[1] # I.e., the mailbox
    msg = email.message_from_file(sys.stdin)
    log_filename = os.path.join(os.path.join(os.path.dirname(__file__), '..'), 'incoming_email.log')
    log_file = open(log_filename, 'a')
    log_file.write('[%s] Received email from %s to %s: ' % (time.strftime('%Y-%m-%d %H:%M:%S'), get_from_email(msg), email_username))
    try:
        handle_email(msg, email_username)
        log_file.write('successfully handled\n')
    except UserException, e:
        log_file.write('exception, %s\n' % e.message)
        new_subject = 'Re: %s' % get_subject(msg)
        new_body = e.message
        our_email = "%s@%s" % (email_username, settings.NOTIFICATION_EMAIL_HOSTNAME)
        their_email = get_from_email(msg)
        send_mail(new_subject, new_body, our_email, [their_email])
    finally:
        log_file.close()

if __name__ == '__main__':
    main()

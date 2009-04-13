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
from cms.permissions import PermissionCache
import email
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist


#TODO error handling (always send back an email, preferrably with same thread, on error)
#TODO attachments? handle html formatting?
#TODO the subject line isn't always getting read

def main():
    permission_cache = PermissionCache()
    msg = email.message_from_file(sys.stdin)
    subject = msg['Subject']
    if msg.is_multipart():
        body = msg.get_payload(0).get_payload()
    else:
        body = msg.get_payload()
    from_email = email.utils.parseaddr(msg['From'])[1]
    to_email = email.utils.parseaddr(msg['To'])[1]
    item_id = to_email.split('@')[0]
    try:
        email_contact_method = EmailContactMethod.objects.get(email=from_email)
    except ObjectDoesNotExist:
        send_mail('Re: %s' % subject, 'Error: Deme could not create your comment because there does not exist a user with email address %s' % from_email, to_email, [from_email])
        return 
    try:
        item = Item.objects.get(pk=item_id)
    except ObjectDoesNotExist:
        send_mail('Re: %s' % subject, 'Error: Deme could not create your comment because there does not exist an item with id %s' % item_id, to_email, [from_email])
        return 
    if not permission_cache.agent_can(email_contact_method.agent, 'comment_on', item):
        send_mail('Re: %s' % subject, 'Error: Deme could not create your comment because you do not have permission to comment on the item with id %s' % item_id, to_email, [from_email])
        return 

    #TODO permissions to view name: technically you could figure out the name of an item by commenting on it here (same issue in cms/views.py)
    comment_name = item.display_name()
    if not comment_name.lower().startswith('re: '):
        comment_name = 'Re: %s' % comment_name
    
    comment = TextComment(item=item, item_version_number=item.version_number, name=comment_name, body=body)
    comment.save_versioned(action_agent=email_contact_method.agent)


if __name__ == '__main__':
    main()

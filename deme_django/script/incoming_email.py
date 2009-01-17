#!/usr/bin/env python

# Set up the Django Enviroment
from django.core.management import setup_environ
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from deme_django import settings
setup_environ(settings)

import cms.models
import email
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist


#TODO permissions (can person even create this comment)
#TODO error handling (always send back an email, preferrably with same thread, on error)
#TODO attachments? handle html formatting?
#TODO the subject line isn't always getting read

def main():
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
        email_contact_method = cms.models.EmailContactMethod.objects.get(email=from_email)
    except ObjectDoesNotExist:
        send_mail('Re: %s' % subject, 'Error: Deme could not create your comment "%s" because there does not exist a user with email address %s' % (subject, from_email), to_email, [from_email])
        return 
    try:
        item = cms.models.Item.objects.get(pk=item_id)
    except ObjectDoesNotExist:
        send_mail('Re: %s' % subject, 'Error: Deme could not create your comment "%s" because there does not exist an item with id %s' % (subject, item_id), to_email, [from_email])
        return 
    comment = cms.models.TextComment(item=item, item_version_number=item.version_number, name=subject, body=body)
    comment.save_versioned(updater=email_contact_method.agent)


if __name__ == '__main__':
    main()

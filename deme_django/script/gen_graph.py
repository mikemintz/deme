#!/usr/bin/env python

# Set up the Django Enviroment
from django.core.management import setup_environ
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from deme_django import settings
setup_environ(settings)

import subprocess
import itertools
from deme_django.cms.models import *
from django.db import models

DOT_PATH = 'dot'

field_name_map = {
    models.ForeignKey: '',
    models.BooleanField: 'Y\\/N',
    models.DateTimeField: 'Date\\/Time',
    models.AutoField: 'Unique Id',
    models.IntegerField: '\\#',
    models.PositiveIntegerField: '\\#',
    models.CharField: 'String',
    models.TextField: 'Long String',
    models.EmailField: 'Email Address',
}

def gen_dotcode(show_fields):
    dotcode = []
    dotcode.append('digraph structs {')
    dotcode.append('  ranksep=0.5; nodesep=0.5; rankdir=TB')
    item_types = all_item_types()
    for item_type in item_types:
        #if item_type not in [Item, Agent, ContactMethod, Transclusion, Document, TextDocument, HtmlDocument, Comment, TextComment, Excerpt, TextDocumentExcerpt]:
        #    continue
        #if item_type.__module__ == 'deme_django.modules.symsys.models' or item_type.__module__ == 'deme_django.modules.webauth.models':
        #    continue
        #if issubclass(item_type, ContactMethod) and item_type not in [ContactMethod, EmailContactMethod, PhoneContactMethod]:
        #    continue
        #if item_type in [DemeSetting, GroupAgent]:
        #    continue
        field_names = []
        field_types = []
        if show_fields:
            for field_name in item_type._meta.get_all_field_names():
                field, model_defined, direct, m2m = item_type._meta.get_field_by_name(field_name)
                if model_defined is None: # defined locally
                    if isinstance(field, models.OneToOneField) or isinstance(field, models.related.RelatedObject):
                        continue
                    if isinstance(field, models.ForeignKey):
                        dotcode.append('  %s:%sTYPE:e -> %s [weight=1,color=red,style=dotted,constraint=false,headport=w,arrowhead=normal,arrowtail=dot];' % (item_type.__name__, field_name, field.rel.to.__name__))
                    field_names.append(field_name)
                    if isinstance(field, models.ForeignKey):
                        field_types.append("[%s]" % field.rel.to.__name__)
                    else:
                        field_types.append(field_name_map.get(type(field), type(field).__name__))
            fieldcols = '{{' + '|'.join(['<%s> %s\\l' % (x,x) for x in field_names]) + '}|{' + '|'.join(['<%sTYPE> %s\\l' % (field_name,field_type) for (field_name,field_type) in zip(field_names, field_types)]) + '}}'
            if field_names:
                label = "{<TOP>%s\\n|%s}" % (item_type.__name__, fieldcols)
            else:
                label = "{<TOP>%s}" % (item_type.__name__,)
            dotcode.append('  %s [shape=record,style=rounded,label="%s"];' % (item_type.__name__, label))
        else:
            label = item_type.__name__
            dotcode.append('  %s [shape=box,style=rounded,label="%s",margin="0.05,0.00"];' % (item_type.__name__, label))
        bases = [x for x in item_type.__bases__ if (issubclass(x, Item) or issubclass(x, Item.Version))]
        for base in bases:
            if show_fields:
                dotcode.append('  %s -> %s [color=blue,style=solid,weight=1,constraint=true,tailport=s,headport=n,arrowtail=inv,arrowhead=none];' % (base.__name__, item_type.__name__))
            else:
                dotcode.append('  %s -> %s [color=blue,style=solid];' % (base.__name__, item_type.__name__))
    dotcode.append('}')
    dotcode = '\n'.join(dotcode)
    return dotcode

def run_dot_to_file(dotcode, filename):
    p = subprocess.Popen([DOT_PATH, '-Tpng'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
    p.stdin.write(dotcode)
    p.stdin.close()
    f = file(filename, 'wb')
    f.write(p.stdout.read())
    f.close()

def main():
    run_dot_to_file(gen_dotcode(show_fields=True), os.path.join(os.path.dirname(__file__), '..', 'static', 'codegraph.png'))
    run_dot_to_file(gen_dotcode(show_fields=False), os.path.join(os.path.dirname(__file__), '..', 'static', 'codegraph_basic.png'))

if __name__ == '__main__':
    main()

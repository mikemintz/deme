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
from deme_django.cms import models

DOT_PATH = 'dot'

field_name_map = {
    'ForeignKey': '',
    'BooleanField': 'Y\\/N',
    'DateTimeField': 'Date\\/Time',
    'AutoField': 'Unique Id',
    'IntegerField': '\\#',
    'PositiveIntegerField': '\\#',
    'CharField': 'String',
    'TextField': 'Long String',
    'IsDefaultField': 'Default Selector',
    'EmailField': 'Email Address',
}

def gen_dotcode(show_fields):
    dotcode = []
    dotcode.append('digraph structs {')
    dotcode.append('  ranksep=1.5; nodesep=1.5;')
    all_models = models.all_models()
    if show_fields:
        all_models = all_models + [models.Item.VERSION]
    for model in all_models:
        field_names = []
        field_types = []
        if show_fields:
            for field_name in model._meta.get_all_field_names():
                field, model_defined, direct, m2m = model._meta.get_field_by_name(field_name)
                field_type = type(field).__name__
                if model_defined == None: # defined locally
                    if field_type in ['OneToOneField', 'RelatedObject']:
                        continue
                    if field_type == 'ForeignKey':
                        dotcode.append('  %s:%sTYPE:e -> %s [weight=1,color=red,style=dotted,constraint=false,headport=w,arrowhead=normal,arrowtail=dot];' % (model.__name__, field_name, field.rel.to.__name__))
                    field_names.append(field_name)
                    if field_type == 'ForeignKey':
                        field_types.append("[%s]" % field.rel.to.__name__)
                    else:
                        field_types.append(field_name_map.get(field_type, field_type))
            fieldcols = '{{' + '|'.join(['<%s> %s\\l' % (x,x) for x in field_names]) + '}|{' + '|'.join(['<%sTYPE> %s\\l' % (field_name,field_type) for (field_name,field_type) in zip(field_names, field_types)]) + '}}'
            if field_names:
                label = "{<TOP>%s\\n|%s}" % (model.__name__, fieldcols)
            else:
                label = "{<TOP>%s}" % (model.__name__,)
            dotcode.append('  %s [shape=record,style=rounded,label="%s "];' % (model.__name__, label))
        else:
            label = model.__name__
            dotcode.append('  %s [shape=box,style=rounded,label="%s "];' % (model.__name__, label))
        bases = [x for x in model.__bases__ if (issubclass(x, models.Item) or issubclass(x, models.Item.VERSION))]
        for base in bases:
            if show_fields:
                dotcode.append('  %s -> %s [color=blue,style=solid,weight=1,constraint=true,tailport=s,headport=n,arrowtail=inv,arrowhead=none];' % (base.__name__, model.__name__))
            else:
                dotcode.append('  %s -> %s [color=blue,style=solid];' % (base.__name__, model.__name__))
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


run_dot_to_file(gen_dotcode(show_fields=True), os.path.join(os.path.dirname(__file__), '..', 'static', 'codegraph.png'))
run_dot_to_file(gen_dotcode(show_fields=False), os.path.join(os.path.dirname(__file__), '..', 'static', 'codegraph_basic.png'))


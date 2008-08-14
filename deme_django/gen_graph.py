#!/usr/bin/env python

# Set up the Django Enviroment
from django.core.management import setup_environ 
import settings 
setup_environ(settings)

import os
import subprocess
import itertools
from deme_django.cms import models

GRAPHVIZ_PATH = '/usr/local/graphviz-2.14/bin'
DOT_PATH = os.path.join(GRAPHVIZ_PATH, 'dot')
#DOT_PATH = 'dot'

field_name_map = {
    'ForeignKey': '',
    'BooleanField': 'Y\\/N',
    'DateTimeField': 'Date\\/Time',
    'AutoField': 'Unique Id',
    'IntegerField': '\\#',
    'CharField': 'String',
    'TextField': 'Long String',
    'IsDefaultField': 'Default Selector',
    'EmailField': 'Email Address',
}

dotcode = []
dotcode.append('digraph structs {')
dotcode.append('  ranksep=1.5; nodesep=1.5;')
for model in (models.all_models + [models.Item.REV]):
#for model in (models.all_models + [x.REV for x in models.all_models]):
    field_names = []
    field_types = []
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
    struct_id = model.__name__
    if field_names:
        label = "{<TOP>%s\\n|%s}" % (model.__name__, fieldcols)
    else:
        label = "{<TOP>%s}" % (model.__name__,)
    dotcode.append('  %s [shape=record,style=rounded,label="%s "];' % (struct_id, label))
    bases = [x for x in model.__bases__ if (issubclass(x, models.Item) or issubclass(x, models.Item.REV))]
    for base in bases:
        dotcode.append('  %s -> %s [color=blue,style=solid,weight=1,constraint=true,tailport=s,headport=n,arrowtail=inv,arrowhead=none];' % (base.__name__, model.__name__))
dotcode.append('}')
dotcode = '\n'.join(dotcode)

p = subprocess.Popen([DOT_PATH, '-Tpng'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
p.stdin.write(dotcode)
p.stdin.close()
f = file(os.path.join(os.path.dirname(__file__), 'static', 'codegraph.png'), 'wb')
f.write(p.stdout.read())
f.close()
#os.system("open graph.png")



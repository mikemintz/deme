from cms.base_viewer import Viewer
from django.http import HttpResponse
from django.template import loader
from django.conf import settings
from urlparse import urljoin
import os
import subprocess
from cms.models import Item

class CodeGraphViewer(Viewer):
    accepted_item_type = Item
    viewer_name = 'codegraph'

    def type_list_html(self):
        """
        Generate images for the graph of the Deme item type ontology, and
        display a page with links to them.
        """
        self.context['action_title'] = 'Code graph'
        # If cms/models.py was modified after codegraph.png was,
        # re-render the graph before displaying this page.
        models_filename = os.path.join(settings.ROOT_DIR, 'cms', 'models.py')
        codegraph_filename = os.path.join(settings.MEDIA_ROOT, 'codegraph.png')
        models_mtime = os.stat(models_filename)[8]
        try:
            codegraph_mtime = os.stat(codegraph_filename)[8]
        except OSError, e:
            codegraph_mtime = 0
        if models_mtime > codegraph_mtime:
            subprocess.call(os.path.join(settings.ROOT_DIR, 'script', 'gen_graph.py'), shell=True)
        code_graph_url = urljoin(settings.MEDIA_URL, 'codegraph.png?%d' % models_mtime)
        code_graph_basic_url = urljoin(settings.MEDIA_URL, 'codegraph_basic.png?%d' % models_mtime)
        template = loader.get_template_from_string("""
        {%% extends layout %%}
        {%% block title %%}Deme Code Graph{%% endblock %%}
        {%% block content %%}
        <div><a href="%s">Code graph</a></div>
        <div><a href="%s">Code graph (basic)</a></div>
        {%% endblock %%}
        """ % (code_graph_url, code_graph_basic_url))
        return HttpResponse(template.render(self.context))

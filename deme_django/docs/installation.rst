Installation
============

Deme is currently only available for checkout at Github:

http://github.com/mikemintz/deme/tree/master

Dependencies
------------
We currently run with Django from SVN, r9673.

http://code.djangoproject.com/svn/django/trunk/django

Because of the table-name size restriction in MySQL, we run on postgresql

* Download tinymce and extract it into a directory called ``deme_django/static/javascripts/tinymce``
* Download an iconset called crystal project (at everaldo) and extract the size folders to a folder called ``deme_django/static/crystal_project``
* ``sudo apt-get install graphviz`` (optional: for gen_graph.py support)
* ``sudo apt-get install python-sphinx`` (optional: for documentation generation)
* ``sudo apt-get install postgresql python-psycopg2``

Apache
------
Here's what I have in my apache ``/etc/apache2/sites-available/deme`` config file::

  <Location "/">
      SetHandler python-program
      PythonHandler django.core.handlers.modpython
      PythonDebug On
      PythonPath "['/var/www/deme', '/var/www/deme/deme_django'] + sys.path"
      SetEnv DJANGO_SETTINGS_MODULE deme_django.settings
  </Location>
  
  Alias /static /var/www/deme/deme_django
  <Location "/static">
      SetHandler None
  </Location>
  
  Options -indexes
  RewriteEngine On
  RewriteRule   ^/static/modules/([^/]*)/(.*)  /static/modules/$1/static/$2  [QSA,L,PT]
  RewriteRule   ^/static/(.*)  /static/static/$1  [QSA,L,PT]


Incoming mail
-------------
You need to route incoming mail to ``incoming_email.py``. I use postfix, so I added
the following to the end of ``/etc/postfix/master.cf``::

  # Deme incoming mail
  deme      unix  -       n       n       -       -       pipe
    flags= user=www-data argv=/var/www/deme/deme_django/script/incoming_email.py

I then added the following to the end of ``/etc/postfix/main.cf``::

  # Deme incoming mail    
  transport_maps = hash:/etc/postfix/deme_transport
  virtual_mailbox_domains = deme.stanford.edu                                                             

I then created a file called ``/etc/postfix/deme_transport`` containing the following::

  deme.stanford.edu    deme:


Installation
============

Deme is currently only available for checkout at Github:

http://github.com/mikemintz/deme/tree/master

Dependencies
------------
We currently run with Django from SVN, r10558.

http://code.djangoproject.com/svn/django/trunk/django

Because of the table-name size restriction in MySQL, we run on postgresql

* Download tinymce and extract it into a directory called ``deme_django/static/javascripts/tinymce``
* Download an iconset called crystal project (at everaldo) and extract the size folders to a folder called ``deme_django/static/crystal_project``
* ``sudo apt-get install graphviz`` (optional: for gen_graph.py support)
* ``sudo apt-get install python-sphinx`` (optional: for documentation generation)
* ``sudo apt-get install python-openid`` (optional: for openid authentication)
* ``sudo apt-get install postgresql python-psycopg2``

Right now, all of the dependencies that are optional are actually required,
since we don't degrade gracefully yet.

Webauth
-------
I did the following commands for Stanford webauth support::

    sudo apt-get install libapache2-webauth
    sudo a2enmod webauth
    sudo mkdir -p /etc/apache2/conf/webauth
    ssh mintz@pod.stanford.edu "wallet -f keytab get keytab webauth/deme.stanford.edu"
    sudo scp mintz@pod.stanford.edu:keytab /etc/apache2/conf/webauth/keytab
    sudo chown root:www-data /etc/apache2/conf/webauth/keytab
    sudo chmod 640 /etc/apache2/conf/webauth/keytab
    ssh mintz@pod.stanford.edu "rm keytab"
    sudo apt-get install krb5-user
    sudo scp mintz@pod.stanford.edu:/usr/pubsw/etc/krb5.conf /etc/krb5.conf

You also need SSL working, which you can figure out from here on Ubuntu:
http://www.tc.umn.edu/~brams006/selfsign.html
http://www.tc.umn.edu/~brams006/selfsign_ubuntu.html
``sudo apt-get install ca-certificates``

Add this to the bottom of ``/etc/apache2/apache2.conf``::
    WebAuthKeyring conf/webauth/keyring
    WebAuthKeytab conf/webauth/keytab
    WebAuthServiceTokenCache conf/webauth/service_token_cache
    WebAuthLoginURL https://weblogin.stanford.edu/login/
    WebAuthWebKdcURL https://weblogin.stanford.edu/webkdc-service/
    WebAuthWebKdcPrincipal service/webkdc@stanford.edu
    WebAuthSSLRedirect on

Apache
------
Here's what I have in my apache ``/etc/apache2/sites-available/deme`` config file::

    <VirtualHost *:80>
        ServerName deme.stanford.edu
        ServerAlias deme
    
        <Location "/">
            SetHandler python-program
            PythonHandler django.core.handlers.modpython
            SetEnv DJANGO_SETTINGS_MODULE deme_django.settings
            PythonDebug On
            PythonPath "['/var/www/deme', '/var/www/deme/deme_django'] + sys.path"
            PythonAutoReload Off
        </Location>
    
        Alias /static /var/www/deme/deme_django
        <Location "/static">
            SetHandler None
        </Location>
        
        Options -indexes
        RewriteEngine On
        RewriteRule   ^/static/modules/([^/]*)/(.*)  /static/modules/$1/static/$2  [QSA,L,PT]
        RewriteRule   ^/static/(.*)  /static/static/$1  [QSA,L,PT]
        
        BrowserMatch ^Mozilla/4 gzip-only-text/html
        BrowserMatch ^Mozilla/4.0[678] no-gzip
        BrowserMatch bMSIE !no-gzip !gzip-only-text/html
        AddOutputFilterByType DEFLATE text/html text/plain text/css text/xml text/javascript application/x-javascript
    </VirtualHost>
    
    <VirtualHost *:443>
        ServerName deme.stanford.edu
        ServerAlias deme
    
        SSLEngine On
        SSLCertificateFile /etc/apache2/ssl/server.crt
        SSLCertificateKeyFile /etc/apache2/ssl/server.key
    
        <Location "/">
            SetHandler python-program
            PythonHandler django.core.handlers.modpython
            SetEnv DJANGO_SETTINGS_MODULE deme_django.settings
            PythonDebug On
            PythonPath "['/var/www/deme', '/var/www/deme/deme_django'] + sys.path"
            PythonAutoReload Off
        </Location>
    
        <Location "/item/webauth/login">
            AuthType WebAuth
            Require valid-user
        </Location>
    
        Alias /static /var/www/deme/deme_django
        <Location "/static">
            SetHandler None
        </Location>
        
        Options -indexes
        RewriteEngine On
        RewriteRule   ^/static/modules/([^/]*)/(.*)  /static/modules/$1/static/$2  [QSA,L,PT]
        RewriteRule   ^/static/(.*)  /static/static/$1  [QSA,L,PT]
        
        BrowserMatch ^Mozilla/4 gzip-only-text/html
        BrowserMatch ^Mozilla/4.0[678] no-gzip
        BrowserMatch bMSIE !no-gzip !gzip-only-text/html
        AddOutputFilterByType DEFLATE text/html text/plain text/css text/xml text/javascript application/x-javascript
    </VirtualHost>

Incoming mail
-------------
You need to route incoming mail to ``incoming_email.py``. I use postfix, so I added
the following to the end of ``/etc/postfix/master.cf``::

  # Deme incoming mail
  deme      unix  -       n       n       -       -       pipe
    flags= user=www-data argv=/var/www/deme/deme_django/script/incoming_email.py

I then added the following to the end of ``/etc/postfix/main.cf``::

  # Deme incoming mail    
  transport_maps = regexp:/etc/postfix/deme_transport
  virtual_mailbox_domains = deme.stanford.edu                                                             

I then created a file called ``/etc/postfix/deme_transport`` containing the following::

  /[0-9]+@deme\.stanford\.edu/    deme:


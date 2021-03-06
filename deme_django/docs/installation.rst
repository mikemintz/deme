Installing Deme
===============

Checking out the source code
----------------------------
Deme is currently only available for checkout at Github:

http://github.com/mikemintz/deme/tree/master

To install Git and learn how to use it, visit:

http://help.github.com/linux-set-up-git/

To checkout Deme, type::

    git clone git://github.com/mikemintz/deme.git

Required Dependencies
---------------------

We have tested Deme on Mac OS X and various distributions of Linux. Our production servers currently run Ubuntu 12.04, which is currently our best supported platform. You will also need to install the dependencies listed below.

PostgreSQL
^^^^^^^^^^
We develop against PostgreSQL from versions 8.3 to 9.2 as our database, although other database engines may be supported. To install PostgreSQL:

* On Ubuntu: ``sudo apt-get install postgresql libpq-dev``
* On Mac OS X: Download http://www.enterprisedb.com/getfile.jsp?fileid=484
* Other OS: Download the database at http://www.postgresql.org/download/

You'll also need to configure a user that Django can use to authenticate. If you don't know how to set up users in PostgreSQL, search Google for setting up PostgreSQL and Django on your OS of choice, and find a tutorial.

But here is what I did for reference::

  $ sudo -u postgres psql template1
  template1=# ALTER USER postgres WITH ENCRYPTED PASSWORD 'MYPASSWORD';
  template1=# \q

I then opened ``/etc/postgresql/8.4/main/pg_hba.conf`` in a text editor as root. I found the line that said ``local all postgres ident``, commented it out, and added a new line underneath that said ``local all postgres md5``. I also found the line that said ``local all all ident``, commented it out, and added a new line underneath that said ``local all all md5``. I also made a ``.pgpass`` file in my home directory that said ``localhost:*:*:postgres:MYPASSWORD`` and ran ``chmod 600 .pgpass``

Python
^^^^^^
We require Python 2.5, 2.6, or 2.7. Python 3 will not work.

* On Ubuntu: ``sudo apt-get install python python-dev``
* On Mac OS X: You probably have it already, but if you don't, try http://python.org/ftp/python/2.6.2/python-2.6.2-macosx2009-04-16.dmg
* Other OS: Find out at http://python.org/download/

Pillow
^^^^^^
We use Pillow to create thumbnails and perform other image alteration tasks. Pillow requires certain imaging libraries to be installed.

* On Ubuntu (12.04 LTS/Raspian): ``sudo apt-get install libtiff4-dev libjpeg8-dev zlib1g-dev \
                                       libfreetype6-dev liblcms2-dev libwebp-dev tcl8.5-dev tk8.5-dev``
* On Mac OS X using Homebrew (http://brew.sh): ``brew install libtiff libjpeg webp littlecms``

For full details please see http://pillow.readthedocs.org/en/latest/installation.html

Virtualenv
^^^^^^^^^^
We use virtualenv to manage Python libraries.

* On Ubuntu: ``sudo apt-get install python-virtualenv``
* On Mac OS X: ``sudo easy_install virtualenv``
* Other OS: Find out at http://www.virtualenv.org/

Once you've installed virtualenv, you can install the python dependencies as follows::

  $ cd /var/www/deme # or wherever you checked it out
  $ cd deme_django
  $ mkdir venv
  $ virtualenv venv
  $ source venv/bin/activate
  $ pip install Django==1.5.1 South==0.8 psycopg2 django-pure-pagination pillow easy-thumbnails ajaxuploader django-forms-bootstrap



TinyMCE
^^^^^^^
We use TinyMCE for WYSIWYG editing in the browser. To install, download the latest package at:

http://tinymce.moxiecode.com/download.php

You'll want to unzip it as ``static/javascripts/tinymce``. To ensure you have the paths correct, you should be able to navigate to ``static/javascripts/tinymce/jscripts``.

Crystal Project icons
^^^^^^^^^^^^^^^^^^^^^
Presently we use Crystal Project icons from everaldo.com in some parts of the UI. To install, download the icons at:

http://www.everaldo.com/crystal/crystal_project.tar.gz

You'll want to unzip it as ``static/crystal_project``. To ensure you have the paths correct, you should be able to navigate to ``static/crystal_project/16x16``.

Postfix
^^^^^^^
We use Postfix to deliver notifications and process incoming emails. Other MTAs may work too, but we give configuration instructions for Postfix. To install:

* On Ubuntu: ``sudo apt-get install postfix``
* On Mac OS X: You should already have it, but if it's not running you'll want to type ``sudo postfix start``
* Other OS: Find out at http://www.postfix.org/

If you want to process incoming mail (optional) in order allow people to reply to action notices and generate comments, you should configure Postfix as follows.

You need to route incoming mail to ``script/incoming_email.py``. I have Deme installed at ``/var/www/deme/deme_django``, so I added the following to the end of ``/etc/postfix/master.cf``::

  # Deme incoming mail
  deme      unix  -       n       n       -       -       pipe
    flags= user=www-data argv=/var/www/deme/deme_django/script/incoming_email.py ${mailbox}

I then added the following to the end of ``/etc/postfix/main.cf``::

  # Deme incoming mail
  transport_maps = regexp:/etc/postfix/deme_transport
  virtual_mailbox_domains = deme.stanford.edu
  virtual_mailbox_base = /var/mail

You may also have to comment out the line in ``main.cf`` that starts with ``mydestination =``.

I then created a file called ``/etc/postfix/deme_transport`` containing the following::

  /.*@deme\.stanford\.edu/    deme:

Optional Dependencies
---------------------

Python-OpenID
^^^^^^^^^^^^^
If you want to enable OpenID for authentication, you will have to install the Python OpenID library.

* On Ubuntu: ``sudo apt-get install python-openid``
* On Mac OS X: ``sudo easy_install python-openid``
* Other OS: Find out at http://openidenabled.com/python-openid/

Graphviz
^^^^^^^^
If you want to generate and display the Deme item type "code graph", you will need to install graphviz.

* On Ubuntu: ``sudo apt-get install graphviz``
* Other OS: Find out at http://www.graphviz.org/

Apache
^^^^^^
If you want to run Deme in the background all the time (instead of using ``./manage.py runserver`` to develop), you'll want to set up a server. I chose to use Apache with mod_wsgi, but anything can work.

First, install Apache and mod_wsgi, and make sure mod_wsgi is enabled.

Make sure ``DJANGO_SERVES_STATIC_FILES`` is false in settings.py to let Apache serve static files.

Here's what I have in my apache ``/etc/apache2/sites-available/deme`` config file::

    <VirtualHost *:80>
        ServerName deme.stanford.edu
        ServerAlias deme

        Alias /static /var/www/deme/deme_django
        <Location "/static">
            SetHandler None
        </Location>

        Options -indexes
        RewriteEngine On
        RewriteRule   ^/static/modules/([^/]*)/(.*)  /static/modules/$1/static/$2  [QSA,L,PT]
        RewriteRule   ^/static/(.*)  /static/static/$1  [QSA,L,PT]

        WSGIScriptAlias / /var/www/deme/deme_django/apache/django.wsgi

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

        <Location "/viewing/webauthaccount/login">
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

        WSGIScriptAlias / /var/www/deme/deme_django/apache/django.wsgi

        BrowserMatch ^Mozilla/4 gzip-only-text/html
        BrowserMatch ^Mozilla/4.0[678] no-gzip
        BrowserMatch bMSIE !no-gzip !gzip-only-text/html
        AddOutputFilterByType DEFLATE text/html text/plain text/css text/xml text/javascript application/x-javascript
    </VirtualHost>

Webauth
^^^^^^^
If you want to enable Webauth, it's kind of tricky. Here is what I did::

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

Setting up Deme
---------------
To set up Deme, you first must copy ``settings.py_EXAMPLE`` to ``settings.py``. Edit ``settings.py`` and make sure the database username/password is correct, and generate a random ``SECRET_KEY``. You'll want to set ``DEFAULT_HOSTNAME`` and ``NOTIFICATION_EMAIL_HOSTNAME`` accordingly for outgoing emails.

If you are using PostgreSQL with username ``postgres`` and database ``deme_django``, you can quickly initialize the database by running::

    script/reset_db.sh

If you want something to be different, just customize this file and run it with your own settings.

You can re-run this file every time you want to reset everything.

To see if everything is working, run::

    ./manage.py runserver

And visit http://localhost:8000/ on your computer. With any luck, Deme will be working!


Upgrading Deme
--------------
When you upgrade Deme (by issuing a new ``git pull``), you should also type ``./manage.py migrate`` to make any necessary updates to the database schema.

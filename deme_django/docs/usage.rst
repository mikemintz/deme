Usage
=====

Customizing a Deme Site
-----------------------

After your Deme site is appropriately set up, many components can be easily customized. Be sure to log in as Admin in order to have permission to make many of these changes.

Change the Site Title and Logo
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Go to your current site's settings. By default, your site will be ``Default Site``. Either look for ``Default Site`` using search or, in the footer, click ``Admin > Sites > Default Site``.
2. Your site settings should show that `Site logo` is "None" and `Site title` is blank.
3. Go to ``Actions > Edit`` to change them.

Tips:
  * To add an image logo, click the ... button to choose or upload an image. To upload a new image, click on ``Create a new image document``, then give your image a name, select your image file to upload, and create the image. The popup window will then close and your image's name will show up in the image logo field. Be sure to save for the logo to show up.
  * To edit the title, simply add a title and save.

Edit the Home Page
^^^^^^^^^^^^^^^^^^

1. From the ``Home Page``, click the ``Edit`` button
2. The editor uses TinyMCE as a WYSIWYG editor. After editing, click ``Save HTML document`` to commit your changes.

Understanding DjangoTemplateDocuments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

DjangoTemplateDocuments allow many different sections of the page to be modified. Here are the important ones:

* ``{% block content %}...{% endblock %}`` addresses the main content area of a page
* ``{% block banner-section %}...{% endblock %}`` addresses the area above the main content area
* ``{% block tabs-section %}...{% endblock %}`` addresses the area between the content and banner-section areas
* ``{% block footer %}...{% endblock %}`` addresses the footer area
* ``{% block logo-section %}...{% endblock %}`` addresses the logo area
* ``{% block sidebar-section %}...{% endblock %}`` addresses the sidebar underneath the logo
* ``{% block custom_css %}...{% endblock %}`` allows insertion of custom CSS styles

To customize your site, you edit these different sections. To learn more about the syntax and technical details, visit [Django's Templates Documentation](https://docs.djangoproject.com/en/1.2/ref/templates/)

Switching the Site Layout
^^^^^^^^^^^^^^^^^^^^^^^^^

1. Go to your current site's settings. By default, your site will be ``Default Site``. Either look for ``Default Site`` using search or, in the footer, click ``Admin > Sites > Default Site``.
2. The ``Default layout`` is used on all pages of the current site. By default, it should be ``Deme Layout``. Click on it to open it for editing.
  * Deme also comes with some sample layouts. By default they are called "Sample Layout" and "Sample Forum Layout". Change the ``Default layout`` to one of them to see what they do.

Editing the Site Layout
^^^^^^^^^^^^^^^^^^^^^^^

In the current layout, edit the different "blocks" to modify the site.

Inserting a banner section::

  {% block banner-section %}
  <div class="banner-section">
    <h3>Generic website banner text</h3>
  </div>
  {% endblock banner-section %}

Adding custom CSS::

  {% block custom_css %}
  .page-layout .logo-section a.logo {
    background: darkred;
  }
  ...
  {% endblock %}

Adding CSS/JS files::

  {% block head_append %}
  <link rel="stylesheet" href="http://www.yoursite.com/stylesheet.css" type="text/css">
  ...
  {% endblock %}

Adding tabs::

  {% block tabs-section %}
  <div class="tabs-section">
    <ul class="nav nav-tabs">
      <li {% ifequal full_path "/welcome" %}class="active"{% endifequal %}><a href="/welcome">Welcome</a></li>
      ...
    </ul>
  </div>
  {% endblock %}

Notice the linked address (in this example "/welcome") is included twice to allow the tab to properly display.

Editing the sidebar::

  {% block sidebar-section %}
  <div class="sidebar-section">
    <div class="panel">
      <div class="panel-heading">
        Resources
      </div>
      <ul>
          <li><a href="#">PDF Link Goes Here</a></li>
          <li>...</li>
      </ul>
    </div>
  </div>
  {% endblock %}

Showing a different footer to non-admins::

  {% block footer %}
    {% if cur_agent.is_admin %}
      {{ block.super }}
    {% else %}
      This is the footer you see when you're not the admin.
    {% endif %}
  {% endblock footer %}

Using a DjangoTemplateDocument as the Home Page (Advanced)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Assuming you've created a DjangoTemplateDocument item you'd like to use as your home page:

1. Go to your current site's settings. By default, your site will be ``Default Site``. Either look for ``Default Site`` using search or, in the footer, click ``Admin > Sites > Default Site``.
2. Edit ``Aliased item`` to be the desired item. Change ``Viewer`` to "djangotemplatedocument" and ``Action`` to "render".

Using a DjangoTemplateDocument instead of an HtmlDocument allows editing of nearly all elements on a page instead of only the contents of the main content area.
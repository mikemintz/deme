Using Deme
==========

Deme is designed for the Chrome, Safari, and Firefox browsers. It should also work in Internet Explore 8 and above, but will have visual inconsistencies.

Interface Guide
---------------

At the top is the Toolbar, which allows users to Log in, Search, etc. By default, the Toolbar is in "Basic Layout", which hides the more advanced functionality. Clicking on the Gear icon at the very top left switches to "Advanced Layout", which introduces more advanced funtionality.

Basic Layout
^^^^^^^^^^^^

Buttons from left to right:

**Gear:** Switches between Basic and Advanced Layout. Hidden if the user does not have permission to view the Advanced Layout.
**Font size:** Allows the user to change the font size for all text on the screen.
**Search:** Searches all items by name and provides a quick link to the Advanced Search interface.
**Login menu:** Displays log in options as well as details for logged in users.

Advanced Layout
^^^^^^^^^^^^^^^

Buttons from left to right not present in the Basic Layout:

**Breadcrumbs:** A list showing the current item (if any), item type, and a link to all items.
**Actions menu:** A menu of actions that apply to the current page.
**Actions icons:** Shortcuts to some of the key actions of the Actions menu.
**Metadata:** Opens the Metadata sidebar, which contains help and information about the current page.



Customizing the Site
--------------------

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

Advanced Customization
----------------------

Hiding `Advanced Layout`
^^^^^^^^^^^^^^^^^^^^^^^^

To change who can see the Advanced toolbar, you'll need to change `Advanced Layout` under `Global Permissions`:

1. Log in as Admin by clicking on the person icon in the top right of the site, then clicking `Login as` and choosing `Admin`
2. Go to the site Admin page by clicking its link in the footer
3. Go to Global Permissions
4. Under `Everyone`, remove the `Advanced Layout` permission by clicking its [-] button and then save. Now the only user who sees the Advanced Layout bar is the Admin.
5. Let's say we want logged in users to see the Advanced Layout bar but not Anonymous users. First, let's allow all users to see the bar by reenabling `Advanced Layout` under `Everyone` by clicking [+] and saving. Now, let's click `Assign a Permission to a User` at the very bottom of the permissions and enter `Anonymous` and then click `Add Collection`. Next, in the newly generated permission area for Anonymous, add a `New Permission`, from its dropdwon menu select `Advanced Layout`, click [-] to disallow, and then finally `Save Permissions`.
6. Now if you visit the site as an Anonymous user, you'll no longer see the Advanced Layout tools.

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

To customize your site, you edit these different sections. To learn more about the syntax and technical details, visit [Django's Templates Documentation](https://docs.djangoproject.com/en/1.5/ref/templates/)

Switching the Site Layout
^^^^^^^^^^^^^^^^^^^^^^^^^

1. Go to your current site's settings. By default, your site will be ``Default Site``. Either look for ``Default Site`` using search or, in the footer, click ``Admin > Sites > Default Site``.
2. The ``Default layout`` is used on all pages of the current site. By default, it should be ``Deme Layout``. Click on it to open it for editing.

  Deme also comes with some sample layouts. By default they are called "Sample Layout" and "Sample Forum Layout". Change the ``Default layout`` to one of them for a very different look and feel.

Editing the Site Layout
^^^^^^^^^^^^^^^^^^^^^^^

In the current layout, edit the different "blocks" to modify the site.

Adding navigation tabs::

  {% block tabs-section %}
  <div class="tabs-section">
    <ul class="nav nav-tabs">
      <li><a href="/">Home</a></li>
      <li><a href="/viewing/group/5">Group</a></li>
      <li><a href="...">...</a></li>
    </ul>
  </div>
  {% endblock %}

Inserting a banner section::

  {% block banner-section %}
  <div class="banner-section">
    <h3>Your banner text goes here</h3>
  </div>
  {% endblock banner-section %}

Adding custom CSS::

  {% block custom_css %}
  .page-layout .logo-section a.logo {
    background: darkred;
  }
  {% endblock %}

Adding CSS/JS files::

  {% block head_append %}
  <link rel="stylesheet" href="http://www.yoursite.com/stylesheet.css" type="text/css">
  {% endblock %}

Editing the sidebar::

  {% block sidebar-section %}
  <div class="sidebar-section">
    <div class="panel">
      <div class="panel-heading">
        Resources
      </div>
      <ul>
          <li><a href="...">Link Goes Here</a></li>
          <li>...</li>
      </ul>
    </div>
  </div>
  {% endblock %}

Showing a different footer to users who aren't the Admin::

  {% block footer %}
    {% if cur_agent.is_admin %}
      {{ block.super }}
    {% else %}
      This is the footer you see when you're not the admin.
    {% endif %}
  {% endblock footer %}

Showing a log in form to visitors who aren't logged in::

  {% block body_wrap %}
    {% if cur_agent.is_anonymous %}
      {% include "demeaccount/required_login_include.html" %}
    {% else %}
      {{ block.super }}
    {% endif %}
  {% endblock body_wrap %}

Hiding chat::

  {% block chat %}{% endblock %}

To show site-wide chat, you'd simply delete that line from a layout.


Using a DjangoTemplateDocument as the Home Page (Advanced)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Assuming you've created a DjangoTemplateDocument item you'd like to use as your home page:

1. Go to your current site's settings. By default, your site will be ``Default Site``. Either look for ``Default Site`` using search or, in the footer, click ``Admin > Sites > Default Site``.
2. Edit ``Aliased item`` to be the desired item. Change ``Viewer`` to "djangotemplatedocument" and ``Action`` to "render".

Using a DjangoTemplateDocument instead of an HtmlDocument allows editing of nearly all elements on a page instead of only the contents of the main content area.

Using Deme with Multiple Sites
------------------------------

Using a single Deme installation with multiple domains/subdomains
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have multiple domains or subdomains that point to your Deme installation, you can show different sites for each by using different Site objects. For instance, let's say you are pointing both `domain1.com` and `domain2.com` to the same Deme installation. Let's also say that you've already set up domain1.com as desired but want `domain2.com` to appear differently.

1. List all sites by, while logged in as Admin, clicking Admin in the footer, then All Sites. There should be one site, the default Site that shows whenever a subdomain doesn't match a particular Site.
2. From here, click **Create a new site**.
3. Set up the site to work with your domain. To do this, change the ``Hostname`` to "domain2.com".
4. Now, the two sites should be using different Sites. Setting the ``Site title`` and ``Default layout`` are simple ways to check to make sure the sites are showing different content.

Restricting items to a single group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have a lot of different sites, you may wish to restrict certain items to certain groups. To do so:

1. From the item you want restricted, go to the Actions menu, then Modify Permissions.
2. Under `Everyone`, add a New Permission. Choose `View Anything` and click on the **[-]** negative permission. This make it so that no one can view the document.
3. Click **Assign a Permission to a Group of Users**. Select the group you'd like to be able to see the document.
4. Under your group, add a New Permission. Choose `View Anything` and click on the **[+]** positive permission. This makes it so that your group can view the document.

If you have many items that you'd like to restrict, it's probably easiest to use collection permissions:

1. Put the items you'd like to restrict into a collection. **Be sure to open the Advanced options and check `Permission Enabled` when doing so.** You can either create a new collection or use the Group's folio.
2. From the collection you want restricted, go to the Actions menu, then Modify Permissions of Members.
3. As with a single item, under `Everyone`, add a New Permission. Choose `View Anything` and click on the **[-]** negative permission. This makes it so that by default users won't be able to see items in your collection.
4. Then click **Assign a Permission to a Group of Users**. Select the group you'd like to be able to see items in your collection.
5. Under your group, add a New Permission, choose `View Anything` and click on the **[+]** positive permission. This makes it so that your group can view the items in the collection.

If you added an item into a collection without checking `Permission Enabled` and want collection permissions to apply to that item, you'll need to change that item's Membership to the collection. To do this, open up the collection, open the Metadata panel, and select Related Data. Open up the list of Child Memberships and make sure all memberships have Permission Enabled checked.
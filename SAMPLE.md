Deme Setup
==========

This document shows how Deme can be set up after being installed on a server.

Hiding `Advanced Layout`
-----------------------

To change who can see the advanced layout tools, you'll need to change `Advanced Layout` under `Global Permissions`:

1. Log in as Admin by clicking on the person icon in the top right of the site, then clicking `Login as` and choosing `Admin`
2. Go to the site Admin page by clicking its link in the footer
3. Go to Global Permissions
4. Under `Everyone`, remove the `Advanced Layout` permission by clicking its [-] button and then save. Now the only user who sees the Advanced Layout bar is the Admin.
5. Let's say we want logged in users to see the Advanced Layout bar but not Anonymous users. First, let's allow all users to see the bar by reenabling `Advanced Layout` under `Everyone` by clicking [+] and saving. Now, let's click `Assign a Permission to a User` at the very bottom of the permissions and enter `Anonymous` and then click `Add Collection`. Next, in the newly generated permission area for Anonymous, add a `New Permission`, from its dropdwon menu select `Advanced Layout`, click [-] to disallow, and then finally `Save Permissions`.
6. Now if you visit the site as an Anonymous user, you'll no longer see the Advaned Layout tools.

Adding users
------------

1. Log in as Admin
2. From the Actions menu, Actions > Create (you can also click directly on the [+] icon)
3. Choose `New person`
4.

Customizing the Site
--------------------

### Site title and logo

1. Log in as Admin
2. Go to your current site settings. By default, your site will be `Default Site`, which you can get to by searching for it.
3. Here you'll be able to edit your sites `Title` and `Logo`.
  * To add an image logo, click the + button and in the popup window, choose a file and create the image document. The popup window will then close and your image's name will show up in the image logo field. Be sure to save for the logo to show up.
  * To edit the title, simply add a title and save.

### Change the home page

1. Log in as Admin
2. From the Home Page, press the Edit button
3. The Home Page is a Django style template. In this case, all we need to do is keep everything inside the `{% block content %}...{% endblock content %}` tags.

### Changing the site's layout

To change how Deme looks, you'll need to change your site's `default layout`:

1. Log in as Admin
2. Add a new `Django template document` or edit an existing one. By default, Deme comes with a `Sample Layout`. If you're making a new layout, be sure to:
  * Set `Override default layout` to true.
  * Have `{% extends "base_layout.html" %}` be the first line of your new layout.
3. Go to your current site settings. By default, your site will be `Default Site`, which you can get to by searching for it.
4. Edit your site's `Default layout` to your new layout. In our case, this will be `Sample Layout`. By default, there is also a "Sample Forum Layout" with another look and feel based on http://communityforum.airhealthprojects.org.
5. Click save and your layout will be updated


### Sample Layout Explained

To customize your site, you edit the `block`s that make up the different sections of the site. To learn more about the syntax and technical details, visit [Django's Templates Documentation](https://docs.djangoproject.com/en/1.2/ref/templates/)

#### Preventing anonymous users from using the site

To prevent anonymous users from viewing the site, we change what's displayed to them using this code:

```
{% block body_wrap %}
  {% if cur_agent.is_anonymous %}
    {% include "demeaccount/required_login_include.html" %}
  {% else %}
    {{ block.super }}
  {% endif %}
{% endblock body_wrap %}
```

#### Banner section

By default, the banner area (block) is left empty. To place content into it, we overwrite the default with the content we want:

```
{% block banner-section %}
  <div class="banner-section">
    <h3>Generic website banner text</h3>
  </div>
{% endblock banner-section %}
```

#### Custom CSS

The easiest way to add your own CSS is through using the `custom_css` block:

```
{% block custom_css %}
  .page-layout .logo-section a.logo {
    background: darkred;
  }
  ...
{% endblock %}
```

If you have existing CSS files or anything else you need to include inside the `<head>`, use the `head_append` block.

#### Tabs

Tabs can be added to a special section underneath the Banner section. Tabs need special syntax to work:

```
<div class="tabs-section">
  <ul class="nav nav-tabs">
    <li {% ifequal full_path "/" %}class="active"{% endifequal %}><a href="/">Welcome</a></li>
    ...
  </ul>
</div>
```

The `{% ifequal full_path "/" %}` syntax highlights that specific tab if you're on the relevant page.

#### Removing Chat

If you don't want a particular block from showing up, you can clear its contents. For example, to remove chat, declare the chat block and leave it empty:

```
{% block chat %}{% endblock %}
```

#### Customizing the Sidebar

To change the sidebar, overwrite the `sidebar-section` block. This is a great way to change the sidebar to link to resources, etc.

```
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
```

#### Hiding the Footer from Anonymous

To prevent non-admins from seeing the footer, we only show the footer to admins.

```
{% block footer %}
  {% if cur_agent.is_admin %}
    {{ block.super }}
  {% endif %}
{% endblock footer %}
```

Welcome to Deme. Deme is a tool for making collaborative websites. This video shows you how to set up your Deme website.

--- Getting Started ---

The first time you open Deme after installing it, it'll look like this. Along the top is the Toolbar, on the left are the logo and some menus, and the rest of the page is content. Let's get started by logging in, clicking on the Login dropdown over here in the top right corner, and selecting Login As.

Since we haven't yet set up user accounts, we can login directly as the Admin. This is something we'll change later so that not everyone will be able to login as Admin. Now that we're logged in, let's go back to the home page.

The toolbar which we used to login with, is in Basic Mode, with tools for viewing the site, like a search button and font size button. We can switch the toolbar to Advanced Mode by clicking on Tools over here on the left. Now we see a lot more tools for editing and setting up the site. One of the most important items is the Actions menu, over here, which we're going going to open and use to Edit the home page.

And here's the Edit view. Let's go ahead and change things around, I'm going to change the first line to "Welcome to Deme, a tool for making collaborative sites". Now I save the document. As you can see, those changes are now on the home page.

Another important part of advanced mode is the Metadata bar, which we can show and hide by clicking on the information icon. There's a lot of information here about what we're looking at. For example, if we open up the Action Notices, it'll show the history of the document, showing how we just edited it. Or if we open up Versions, we can see how the page looks before we edited it. There's also Help, which tells you more about the type of document you're looking at.

--- Customizing Your Site ---

Okay so now let's change the title of the site to something else. First, let's click on Admin in the footer. We want to change our site settings, so click "Edit Current Site". This takes us directly to editing the current site. Now let's scroll down until we get to Site Title. Let's change that to "Deme Demo" and save. Now we see that the title has changed both on the left and on the tab. Perhaps we also have a logo we'd like to use. Let's edit the site again, scroll down to Site logo, and click on the dot dot dot.

Since we don't have any image documents yet, let's go ahead and create a new one. Let's call it "Deme Demo Logo", find the file, then create the image document. Notice that now Site logo is set to Deme Demo Logo. Let's save and now our new image logo is there.

--- Adding users ---

Now let's go ahead and add some new users.

- Go to Actions > Create and select "New person". The `Name` is what's displayed publicly throughout the site and in general is the person's full name. You can also add a picture of that person in the same way that you uploaded a logo. Name your person something you'll remember.

- Let's go ahead and make a second person. So that we'll have enough to make a group.

New Groups
----------

Now let's make a group to put our new users in.

- Go to Actions > Create and select "New group". Like persons, groups have names and an image. I'm going to name mine the Agora and give it an image.

- Create the group. After creating it, you'll see the group page, which doesn't have anyone on it yet.

- Let's add the people we just created. Go to Actions > Insert an item which opens a popup. Start typing in the name of your first person and then click submit when she appears. Do so for your second person.

- Now you should see two members on your group page, and if photos have been set, their photos.

New Poll
--------

Now let's go ahead and make a poll for our group to take.

- Go to Actions > Create and choose New agree disagree poll.

- Name your poll as appropriate. I'm going to name mine "Philosophy Poll". Under `question` I'm going to put "Do you adhere to these philosophical statements?"

- Most importantly, each poll needs to have a group it's for. Under `Eligibles` I'm going to select my group, Agora. There are also options to control if people can see who has voted and to allow people to change their answers. Create the poll.

- Now we need to add propositions to the poll. Go ahead and click "Add a Proposition".

- Let's say I want the first one to be about wisdom. For the `item name`, I would put "Wisdom", under `Summary text` I would put "Wisdom means knowing that you know nothing", and in the `Body` I would put further details about the proposition, like why the statement might be correct, why not, etc. Click create after you're done typing in your details.

- Now you'll see your first proposition listed, with the name and summary visible and the details listed under `Read More`. You'll also see Poll Results, of which we currently have none. Go ahead and create at least one more proposition in the same way.

Taking the Poll
---------------

Let's now try taking the poll.

- In the toolbar, click the Person icon to open the Account menu. Click Login As and choose one of your group members and go back to the previous page.

- Notice that all of the administrative options are gone and you simply have a method to take the poll. Agree and disagree as you will and enter a personal statement if you'd like. Then submit.

- Now you'll be able to see the poll results so far and if you had selected to allow people to take the poll again when making it, you'd be able to retake the poll.


Creating a discussion board
---------------------------

Now let's try adding a discussion board.

- Go to Actions > New item and choose New Discussion Board. I'm going to Name it "Agora Discussion Board". I'm going to go ahead and kick it off.

Making a new page
-----------------

- Go ahead and log in as admin.

- Go to Actions > New item and choose HTML document. Put a memorable page title in Item name like "Exercise Experts" and use the WYSIWYG editor to create your page. When you're done making it, go ahead and click create.

adding the socrates link to the side menu only scratches the surface of what we can do with the layout. For example, I've prepared a layout in advance that uses custom styles to really change how everything looks. To Learn more about the layout, please see the Technical Deme Guide, found under info, help, technical deme guide.

Uploading a PDF/DOC/other file
------------------------------

- Go to Actions > New item and choose new file document. Name it something memorable and choose your file and create. This uploads the file to the server.

The group folio
---------------

Each group has a "folio" of items that can contain any items. Let's go ahead and put our poll, new page, and file upload in the folio.

- Go to your group. The easiest way is probably to search for the group.

- In the Group Folio table, clik the small Add button. You can add your items to the folio this way.

Editing the home page
---------------------

This section assumes you know a little bit about HTML

- Let's go back to the home page and click the edit button.

- The Home Page is written in Django templated HTML, so let's take a look. Please note that all the edits you make should be between the {% block content %} and {% endblock content %} tags. Let's go ahead and change it to something very simple, for example `{% block content %} Hello World {% endblock content %}`

- Now when you open up the home page, you'll see that all the text that used to be there is now simply "Hello World"

Changing the Layout
------------------

With Deme, you can customize the look and feel of the entire site by changing the layout. We've got a ready made layout that we'll use.

- Open the Default Site we used earlier to customize title and logo.

- Set the default layout to `Sample Forum Layout`, then save. Now the site should look more like the discussion site.

- This new layout also makes it so that login is required to see the site so if you log out, you'll need to log in to see anything. Try using "todd" or "mike" with blank password to get in if you get logged out.

Editing the Layout
------------------

This section assumes you know a little bit about HTML

- Let's go ahead and change the tabs to link to our poll, discussion board, and new page. In order to do so, we'll need the links of all those pages. We can change the links by editing the Layout. Search for "Sample Forum Layout" and edit it.

- The section we are interested in is {% block tabs-section %}. Scroll down until you reach it.

- You should see a number of <li> tags that look like `<li {% ifequal full_path "/" %}class="active"{% endifequal %}><a href="/">1: Welcome</a></li>`. What we need to do here is to change the links and title to those we want.

- More specifically, replace both "/" with the url of the page we're interested in, being sure to remove the http://www.domain.com portion.

- Save after you've made your changes

Likewise, update the `{% block sidebar-section %}` in order to change what's listed under Resources.

- Look for `<a href="#">PDF Link Goes Here</a>` and change it to fit your needs. Copy and paste as many new list items (`<li>`) as you need.

For more information about editing the Layout, see the SAMPLE.md file.


Testing Procedure
-----------------

Modify the layout
Change permissions
Add new members
Create a new poll
Take the poll
Add multiple items to a collection
Search for items


Securing the Site
-----------------

Now that we've got
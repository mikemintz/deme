Welcome to Deme. Deme is a tool for making collaborative websites.

--- Getting Started ---

The first time you open Deme after installing it onto your web server, it'll look like this. Along the top is the Toolbar. Let's go ahead and log in by clicking on the Login dropdown and selecting Login As.

We can directly login as Admin since we haven't set up user accounts or otherwise secured the site yet. Let's go ahead and get back to the home page.

The toolbar is currently in Basic Mode, which besides letting people login, also contains search and accessibility functionality. The toolbar also has an Advanced Mode that we can turn on by clicking on Tools. Now we can take more actions like editing the home page. This we do by going to Actions and then Edit.

Let's go ahead and change things around a bit, then save the document. As you can see, our changes are now on the home page.

Also, in advanced mode, there's the Metabar pane that we can show by clicking on the information icon. It'll show use useful information like action notices that we just edited the page, versions so that we can see what the page looked like before we edited it, and help for further information.

--- Customizing Your Site ---

Okay so now let's change the title of the site to something different. First, let's click on Admin in the footer. We want to change our site settings, so click "Edit Current Site". This takes us directly to editing the current site. Now let's scroll down until we get to Site Title. Let's change that to "Deme Demo" and save. Now we see that the title has changed both on the left and on the tab. Perhaps we also have a logo we'd like to use. Let's edit the site again, scroll down to Site logo, and click on the dot dot dot.

Since we don't have any image documents yet, let's go ahead and create a new one. Let's call it "Deme Demo Logo", find the file, then create the image document. Notice that now Site logo is set to Deme Demo Logo. Let's save and now our new image logo is there.

--- Adding users ---

Now let's go ahead and add some new users.

- Go to Actions > New item and select "New person". The `Name` is what's displayed publicly throughout the site and in general is the person's full name. You can also add a picture of that person in the same way that you uploaded a logo. Name your person something you'll remember.

- Let's go ahead and make a second person. So that we'll have enough to make a group.

New Groups
----------

Now let's make a group to put our new users in.

- Go to Actions > New item and select "New group". Like persons, groups have names and an image. Name your group something you'll remember, and if you'd like, give it an image.

- Create the group. After creating it, you'll see the group page, which doesn't have anyone on it yet.

- Let's add the people we just created. Go to Actions > Insert an item which opens a popup. Start typing in the name of your first person and then click submit when she appears. Do so for your second person.

- Now you should see two members on your group page, and if photos have been set, their photos.

New Poll
--------

Now let's go ahead and make a poll for our group to take.

- Go to Actions > New item and choose New agree disagree poll.

- Name your poll as you like, perhaps something like "Exercise Poll". Under `question` you could put something like "How do you feel about exercise?"

- Most importantly, each poll needs to have a group it's for. Under `Eligibles` type in the group you just created. There are also options to control if people can see who has voted and to allow people to change their answers. Create the poll.

- Now we need to add propositions to the poll. Go ahead and click "Add a Proposition".

- Let's say I want to find out whether people think that government ought to provide free exercise classes. For the `item name`, I would put "Free Exercise Classes", under `Summary text` I would put "Should government be mandated to provide free exercise classes for all US citizens", and in the `Body` I would put further details about the proposition, like why it might be a good idea, why it might not be, etc. After you've completed adding details to your proposition hit Create.

- Now you'll see your first proposition listed, with the name and summary visible and the details listed under `Read More`. You'll also see Poll Results, of which we currently have none. Go ahead and create at least one more proposition in the same way.

Taking the Poll
---------------

Let's now try taking the poll.

- In the toolbar, click the Person icon to open the Account menu. Click Login As and choose one of your group members and go back to the previous page.

- Notice that all of the administrative options are gone and you simply have a method to take the poll. Agree and disagree as you will and enter a personal statement if you'd like. Then submit.

- Now you'll be able to see the poll results so far and if you had selected to allow people to take the poll again when making it, you'd be able to retake the poll.

Creating a discussion board
---------------------------

Now let's try adding a discussion.

- Go to Actions > New item and choose New Discussion Board. Name it "Exercise Discussion Board"

Making a new page
-----------------

- Go ahead and log in as admin.

- Go to Actions > New item and choose HTML document. Put a memorable page title in Item name like "Exercise Experts" and use the WYSIWYG editor to create your page. When you're done making it, go ahead and click create.

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

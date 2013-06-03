Deme Demo
=========

This document describes how to demo Deme for an audience each with their own fresh installation of Deme.

Interface
---------

- Open up Deme. Inform participants that Deme is designed for Chrome, Safari, and Firefox. It should work in IE8 and higher, but will look better in newer, more modern browsers.

- At the top is the toolbar, it lets you log in, search, edit, and more. Right now it's in "basic mode". Try clicking on the Gear icon on the left to switch to "advanced mode". You should see a new list of pages, these are breadcrumbs that show you what type of document you're looking at. There's also a new Actions dropdown menu.

- There's also a Metadata Pane that is opened with the Info icon on the right. This tool gives you useful information about the page you're looking at.

Logging in
----------

- So let's say we want to edit the site. To do so we need to log in.

- Use the toolbar to log in. Click the Person icon on the right. Click "Login As". For this demo site, you'll be able to directly login as Admin. Do so now by clicking on Admin.

- You should see a screen that confirms you've logged in.

Site title and logo
-------------------

- Let's go ahead and change the site's name. Search for "Default Site" and then Actions > Edit.

- Currently the title is blank, so by default "Deme" is displayed. Change that so something you like, preferably short, then Save. For example, I'm going to change mine to "Cats".

- The site title should now be changed across all pages. You can also upload a logo. Edit the Default Site again, then click the Plus sign next to Logo. This opens a popup that lets you upload a photo. Go ahead and do so, clicking "create image document", then save the site. You should see the picture as your logo throughout the site.

We'll look at editing the site further later in the demo.

New Users
---------

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

Making a new page
-----------------




Editing Items
-------------

- Let's go back to the home page to edit it.

- Now when we look at the Actions dropdown menu, there are a lot of actions that weren't there before. The one we're interested in is Edit, so let's click that.

- The Home Page is written in HTML, so let's take a look. Please note that all the edits you make should be between the {% block content %} and {% endblock content %} tags. Let's go ahead and change it to something very simple, for example `{% block content %} Hello World {% endblock content %}`

- Now when you open up the home page, you'll see that all the text that used to be there is now simply "Hello World"

Editing the Layout
------------------
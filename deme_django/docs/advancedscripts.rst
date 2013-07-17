Advanced Scripts
================

Creating Users from CSV File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The script file is located at /script/add_agents_from_csv.py. To use it, upload a CSV file to the server and invoke the script with the CSV file as argument.

The CSV file should be formatted "name", "password", "group". The group must be created ahead of time. For example, to add users to the group "Deliberation Group Alpha", the CSV file might look like::

  Mike,secretpassword,Deliberation Group Alpha
  Todd,anothersecretpassword,Deliberation Group Alpha
  Michael,differentpassword,Deliberation Group Alpha

Then each user would be able to login with their name and password.
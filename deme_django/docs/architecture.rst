Deme Architecture
=================

Back-end (items)
----------------

Overview
^^^^^^^^
Most persistent data in Deme is stored in "items". An item is an instance of a particular "item type". This is in parallel to object-oriented programming where instances (items) are defined by classes (item types), and in parallel to filesystems where files (items) are defined by file types (item types). The Deme item types form a hierarchy through inheritance, so if the Person item type inherits from the Agent item type, then any item that is a person is also an agent. Every item type inherits from the Item item type (which corresponds to the Object class in many programming languages). We allow multiple inheritance, and use it occasionally (e.g., TextComment inherits from both Comment and TextDocument).

Database
^^^^^^^^
We use ORM with multi-table inheritance. There is a database table for every item type, and a row in that table for every item of that item type. For example, if our entire item type hierarchy is Item -> Agent -> Person, and our items are Mike[Person] and Robot[Agent], then there will be one row in the Person table (for Mike), two rows in the Agent table (for Mike and Robot), and two rows in the Item table (for Mike and Robot).

Fields
^^^^^^
Every item type defines the "fields" relevant for its items, and item types inherit fields from their parents. As a simple example, imagine Item defines the "description" field, Agent defines no new fields, and Person defines the "first_name" field. Therefore every person has a description and a first_name. The columns in each table correspond to the fields in its item type. So if the Mike item has description="a programmer" and first_name="Mike", then his row in the Item table will just have description="a programmer", his row in the Agent table will have no fields (because Agent did not define any new fields), and his row in the Person table will have first_name="Mike".

Field types
^^^^^^^^^^^
Every field has a type that corresponds to the types we can store in our database. The basic types are things like String, Integer, and Boolean. It is important to realize that fields are *not* items. So if Mike's first_name field is of type String, it cannot be referred to as an item itself. You cannot store entire items as fields, but you can have fields that point to other items (foreign keys in database-speak, pointers/references in programming, links in filesystems). If we wanted to "itemize" the first_name field, we could make a new FirstName item type and have the Person's first_name field be a pointer to an first_name item. In the case of first_name, however, this is not particularly useful, and it just adds more overhead (and makes versioning difficult, as we'll see later on). Pointer fields are more useful for defining relationships between legitimate items. For example, the Item item type has an "creator" field pointing to the agent that created the item.

Pointers do not represent an exclusive "ownership" relationship. I.e., just because an item pointed to the agent that wrote it, this does not prevent other items from pointing to that agent. Multiple items can point to a common item.

Fields cannot store data structures like lists. If you want to express X has many Y's,  rather than storing all the Y's in the X row, you should itemize the Y's, and have each Y point to the X that it belongs to. For example, an Agent has many ContactMethods. So rather than storing the ContactMethods as fields inside each Agent, we make ContactMethod an item type, and give it an "Agent pointer" field. So the contact methods for agent 123 are represented by all of the ContactMethods that have agent_pointer=123.

The most important field is the id field (primary key in database-speak, memory address of the object in programming, inode number in filesystems). Every item has a unique id, an auto-incrementing integer starting at 1. Items share the same id with their parent-item-type versions (so Mike's row in the Person table has the same id as Mike's row in the Agent table and Item table). Pointer fields are effectively references to the id of the pointee. It is important that the id field never change so that there is always a single reliable way to refer to a particular item. No other field is guaranteed to be unique among all items (although some item types define unique fields within that item type, such as PasswordAuthenticationMethod's unique username).

Some fields are specified as immutable, which means once they are set, they cannot be changed. The id field is a prime example of an immutable fields, but other fields like creator and created_at are immutable as well.

Versioning
^^^^^^^^^^
For every item type table, there is a dual "revisions" table. So in our previous example, in addition to the Item, Agent, and Person tables, we now have ItemVersion, AgentVersion, and PersonVersion tables. These tables store the exact same fields as their original non-versioned tables, with a few exceptions:

* Each itemversion has a pointer to the item it is a version of.
* Each itemversion has a version_number field, an integer starting at 1 and incrementing each time a new version is made. The largest version number always corresponds to the latest version.
* Immutable fields are not stored in the version table. For example, although creator and created_at are fields in the Item table, they are not fields in the ItemVersion table since they cannot change.
* Uniqueness constraints are not propagated from the regular table to the version table. For example, if we had the constraint that there can only be one Person for every email address (i.e., email addresses are unique), then it wouldn't make sense to enforce that in the revisions table, since version 1 and version 2 of Mike might have the same email address.

So apart from these differences, each itemversion stores the exact same fields as the regular item. Every time a change is made to the regular item, a snapshot is taken and a new itemversion is created with an increased version number. So when the Mike item is changed, Mike's rows in the Item, Agent, and Person table are updated, and those updates are copied over to the ItemVersion, AgentVersion, and PersonVersion tables, so that we can refer to the past.

Here is the major caveat. Imagine there is a student and a class. We must represent their relationship with a third item type, the ClassMembership, since classes cannot store arrays of students, and students cannot store arrays of classes. If the student joins the class, a ClassMembership is created. Ideally, we'd like to be look at the previous roster of the class, but since the class roster is just composed of ClassMemberships that point to the class, there is no way to refer to a previous version. A possible solution is to refer to the entire state of items at a particular time step, which is possible since we can compute what versions were around at any given moment, but that gets convoluted. For now, just assume that versioning only plays well with regular fields, and does not work on data structures created via relationship tables.

Deleting items
^^^^^^^^^^^^^^

There are two ways of deleting items: trashing and deleting. Neither of these methods removes any rows from the database. Trashing is recoverable, deleting is not. The user interface ensures that trashing happens before deleting.

* **Trashing:** If an agent trashes an item, it sets the trashed field to true. An agent can recover the item by untrashing it, which sets the trashed field back to false. Each time this happens, the version does not change, but a TrashComment or UntrashComment is automatically generated to log when the item was around. Trashed items can still be viewed and edited as normally. The major difference between a trashed and untrashed item is that when an item is trashed, it will not be returned as the result of queries (unless the query specifically requests trashed items). For example, when you look at the list of students in a class, it will only show students that are untrashed with classmemberships that are untrashed.
* **Deleting:** We have not implemented deleting yet. The idea is that after an item is trashed, you can permanently blank out all of its fields (and the fields in its versions) so that it is impossible to recover (but keep trashed=true). The technical difficulty of this is coming up with a systematic way to blank every field without causing database constraint violations. For example, the database might specify that the name field cannot be blank. A workaround for this problem is to set each field to a sentinel allowed value, like "[BLANK]". This breaks down with uniqueness constraints and foreign-key constraints: if Person has a unique email field that cannot be blank, what do you set the deleted person's email field to? You cannot set it to "[BLANK]" since more than one person will have the same email field. With foreign-key constraints, what do you set the creator pointer to?

Things stored outside the database
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Not every bit of persistent data is stored in the database in item fields. Here are the exceptions so far:

* Uploaded files (like the files corresponding to FileDocuments) are stored on the filesystem in the static files folder so they can be stored more efficiently (databases are not good for binary data) and so they can be served quickly by the webserver without going through Deme. The FileDocument item type has a string field that represents to the path on the filesystem to the file.
* Item type definitions are stored as code, not in the database. The fact that Person is a subtype of Agent and defines the first_name field is inferred from the Deme code, and should not be read from the database. In the future, we are considering creating a "ItemTypes" table that stores one row per item type (the size would remain fixed as long as the code does not change), and this way, we could refer to item types (one good example is an admin might want to create a permission for another user to create new items of a specified type). This would also be a good place to store dynamic settings specific to each item type (like default permissions). Since the item type definitions are static, it seems like we never need this ability, and can always emulate it with more code.

Core item types
^^^^^^^^^^^^^^^
TODO: keep revising documentation starting here.
Below are the core item types and the role they play (see the full ontology at http://deme.stanford.edu/item/codegraph).

* **Item:** Everything is an item. It gives us a completely unique id across all items, and defines some fields common to all items, such as updated_at and description. I'm not sure if description is a good idea though... I'm troubled by the fact that we must come up with a description for every GroupMembership. TODO explain new name/description idea
* **Agent:** An Agent is an Item that can "do" things. This is important for authentication (only agents can log in), and permissions (agents are the entities we assign permissions to). Also, if there is an author pointer for an item, it should point to an agent. Not all agents are people: agents could be bots or groups too. An example of using a group as an agent is when you want to act on behalf of an organization. For example, imagine we have a group called Alaska Democratic Party. It might create a document called "Party Platform", and it would be desirable to show that the document was authored by Alaska Democratic Party, rather than some random guy who wrote the prose. Also, we might want to use permissions to give this group the ability to cast one vote in the national convention. Later on, when we work more on authentication, we will give particular persons the ability to authenticate on behalf of the group and do these sorts of actions.
* **Account:** An Account is an Item that represents some credentials to login. For example, there might be an account representing my Facebook login, an account representing my WebAuth login, and an account representing Todd's OpenID login. Every Account points to the Agent it belongs to. Rather than storing the login credentials in a particular Agent, we allow agents to have multiple accounts, so that they can login different ways. Accounts can also be used to sync profile information through APIs. There will be subclasses of Account for each different way of logging in (WebAuthAccount, FacebookAccount, etc.)
* **AnonymousAccount:** An AnonymousAccount is an Account that is used whenever someone has not authenticated yet. There should be exactly one AnonymousAccount, which corresponds to a single anonymous agent. Thus, whenever someone is not logged in, they are effectively this one anonymous agent. Thus, everywhere in Deme, the website visitor is always represented by an Agent, whether it is the actual person or just the anonymous agent.
* **Person:** A Person is an Agent that has fields like first name, last name, email address, etc. Depending on how we sync with other profiles, we might want to extract a lot of this to a new Profile class.
* **Collection:** A Collection is an Item that represents a set of other items. Collections just use pointers to represent their contents, so multiple Collections can point to the same contained items. Since fields cannot store arrays, Collection contents are represented by ItemToCollectionRelationships.
* **Folio:** A Folio is a Collection that belongs to a Group.
* **Group:** A Group is an Agent that has a folio and a list of member Agents (through the GroupMemebership item type).
* **Document:** A Document is an Item that is meant to be a collaborative work. It is abstract in practice (you should always use a subcl
* **TextDocument:** A TextDocument is a Document that has a text field (that stores any unicode or ascii text right now).
* **FileDocument:** A FileDocument is a Document that stores a file on the filesystem (could be an MP3 or a Microsoft Word Document).
* **Comment:** A Comment is a TextDocument that represents discussion about a particular version of a particular item. A reply to a comment is represented by another comment commenting on the original comment.
* **HtmlDocument:** An HtmlDocument is a TextDocument that renders the text field as HTML.
* **DjangoTemplateDocument:** A DjangoTemplateDocument is a TextDocument that stores Django template code that can display a fully customized page on Deme. Use this for static content, although it can be dynamic since it's a Django template.
* **Relationship:** A Relationship is an Item that represents a relationship between two Items. It has a pointer to the first item and a pointer to the second item (although we're still deciding on where these pointers will be stored).
* **GroupMemebership:** A GroupMemebership is a Relationship between an Agent and a Group representing the agent's membership in the group.
* **CollectionMembership:** A CollectionMembership is a Relationship between an Item and the Collection representing the face that the Collection contains the Item.

There are also item types defined for permissions and URL aliasing described in the next two sections (they are still full item types, but they require much more explanation).

Permissions
^^^^^^^^^^^
Permissions define what Agents can and cannot do, both in general, and with respect to specific Items. Hard-coded into Deme will be a list of abilities (as strings), such as CanCreateGroup and CanRenameThisGroup. Using the item types described below, Deme will take the currently authenticated Agent (anonymous or not), and decide whether it has the required ability to complete the requested action. Abilities are not just checked before doing actions, but they can also be used to filter out items on database lookups. For example, if my viewer is supposed to display a list of items I am allowed to see (because I have the CanSeeItem ability), it will need to use permissions to filter out inappropriate results.

Below are the item types relevant to permissions.

* **AgentPermission:** An AgentPermission is a Relationship between an Agent and an Item, specifying a particular Role that holds between them. For example, one might create an AgentPermission between Mike and Mike's Diary with the Role "creator", which would give me all the abilities I need to manage this item. If the item field is left blank (i.e., a Relationship between Mike and nothing), then it represents a global role assignment. For example, you might create an AgentPermission between Mike and nothing with Role "site admin" to make Mike the admin of the entire Deme installation.
* **GroupPermission:** An GroupPermission is a Relationship between a Group and an Item, specifying a particular Role that holds between the users of that group and the Item. It works the same exact way as AgentPermission, except that the abilities are not given to the Group agent, but instead to all of the agents in the Group. So if the Alaska Democratic Party is given a GroupPermission in order to vote, all of the members get that ability, but not the group as an agent. In contrast, if the Alaska Democratic Party is given an *AgentPermission*, the group gets the ability and none of the members do.

Abilities between an Agent and an Item (or "nothing" for global abilities) are decided with the following rules, executed in order:

# Look at all of the AgentItemRoleRelationships that hold between this Agent and this Item. If any of them have ability X granted, then grant ability X. If none of them have ability X granted, and any of them have ability X denied, then deny ability X. Otherwise, continue at the next step.
# Look at all of the GroupItemRoleRelationships that hold between any of this Agent's groups and this Item. If any of them have ability X granted, then grant ability X. If none of them have ability X granted, and any of them have ability X denied, then deny ability X. Otherwise, continue at the next step.
# Look at all of the AgentItemRoleRelationships that hold between agent=null and this Item (this represents everyone permissions for this Item). If any of them have ability X granted, then grant ability X. If none of them have ability X granted, and any of them have ability X denied, then deny ability X. Otherwise, deny ability X.

URL Aliases
^^^^^^^^^^^
In order to allow vanity URLs (i.e., things other than /item/item/5), we have a system of hierarchical URLs. In the future, we'll need to make sure URL aliases cannot start with /item/ (our base URL for viewers), /static/ (our base URL for static content like stylesheets), or /meta/ (our base URL for Deme framework things like authentication). Right now, if someone makes a URL with one of those prefixes, you just cannot reach it (it does not shadow the important URLs).

* **ViewerRequest:** A ViewerRequest is an Item that represents a particular action at a particular viewer (basically a URL, although its stored more explicitly). It specifies a viewer (just a string, since viewers are not Items), an action (like "view" or "edit"), an item that is referred to (or null for the entire collection), and a query_string if you want to pass parameters to the viewer.
* **Site:** A Site is a ViewerRequest that represents a logical website with URLs. A Site can have multiple SiteDomains, but ordinarily it would just have one (multiple domains are useful if you want to enable www.example.com and example.com). Multiple Sites on the same Deme installation share the same Items with the same unique ids, but they resolve URLs differently so each Site can have a different page for /mike. If you go to the base URL of a site (like http://example.com/), you see the ViewerRequest that this Site inherits from.
* **SiteDomain:** A SiteDomain is an Item that represents a hostname for a Site.
* **CustomUrl:** An CustomUrl is a ViewerRequest that represents a specific path. Each CustomUrl has a parent ViewerRequest (it will be the Site if this CustomUrl is the first path component) and a string for the path component. So when a user visits http://example.com/mike/is/great, Deme looks for an CustomUrl with name "great" with a parent with name "is" with a parent with name "mike" with a parent Site with a SiteDomain "example.com".

Front-end (viewers)
-------------------

Overview
^^^^^^^^
A viewer is Django class that processes browser or API requests. Any URL that starts with /item/ is routed to a viewer. Each viewer defines the item type it can handle, although multiple viewers could theoretically handle the same item type (you could have ItemViewer and SuperItemViewer which both handle items). There should be a default viewer for every item type, and if there is none, then the default viewer of the superclass should be used. Viewers that handle item type X always handle items that are in subclasses of X (except in the case of editing/updating, in which case they can only handle superclasses, although we still need to fix some behavior for this "downcasting" ability).

URLs
^^^^
Our URLs are restful. Every URL defines a viewer, an action, a noun (or none for actions on the collection), a format, an optional parameters in the query string. Here are some example URLs:


* /item/item (item viewer, default "list" action, default "html" format)
* /item/person/new.xml (person viewer, new action, xml format)
* /item/person/1 (person viewer, default "show" action, person with id=1 is the noun, default "html" format)
* /item/person/1/edit.json?version=5 (same as above, but json format, edit action, and version 5)

Actions
^^^^^^^

Every viewer URL defines a set of actions it responds to. The basic actions that most viewers should respond to are list, show, edit, and delete (when we figure out deleting things, which we still need to discuss). Actions are divided into two groups: those that take nouns (which are always item ids) called "entry" actions, and those that do not take nouns called "collection" actions. In order to make URLs unambiguous, item ids must be numbers, and action names can only be letters (although we can decide what other characters to allow, such as underscores and dashes).
 
An action corresponds to a single Python function. If you visit /item/item/list, Deme will call the collection_list method of the ItemViewer class. If you visit /item/person/5/show, Deme will call the entry_show method of the PersonViewer class. Actions return the HTTP response to go back to the browser. Actions can call other actions from other viewers to embed views in other views (for example, the DocumentViewer might want to embed a view from the PersonViewer to show a little profile of the author at the top).

Nouns
^^^^^
Entry actions take in a noun in the URL, which is the unique id of the item it acts upon. If viewers need more information (say I submitted a form that specified multiple people I wanted to add to a group), the data is passed in the query string (or the HTTP post data), and the data required is up to the specific viewer. The only query string parameter that is reserved right now is "version" which specifies a specific version of the item the viewer is acting on.

Formats
^^^^^^^
An additional parameter is passed in defining the response format, like HTML or XML. The default is HTML. Viewers ignore this now, but it's easy to act upon it. I might add something where viewers have to register which formats they respond to, so that we can display error messages when you type the wrong format rather than ignoring it. Note that the format only specifies the response format. The request format (what the browser sends to the server) is always the same: all parameters encoded in the URL or the HTTP post data. We will only be using HTTP as the transport for viewers (although we can define things that accept emails and SSH and other protocols, they just won't be called viewers).

Authentication
^^^^^^^^^^^^^^
Whenever a visitor (or another web service or bot) is at an action of a viewer, he has an authenticated account, and through that account, is an Agent. If a visitor has not authenticated, they'll be using the AnonymousAccount, and will be the anonymous agent. We will support various ways of authenticating via the different subclasses of Account.

DjangoTemplateDocuments
^^^^^^^^^^^^^^^^^^^^^^^
There is a DjangoTemplateDocument viewer right now, which accepts DjangoTemplateDocuments, and when viewed with the show action, it renders the DjangoTemplateDocument as HTML (or whatever format) straight back to the browser. This allows users to add web content that is not really used by a viewer, so they can fully customize the user experience. By using DjangoTemplateDocuments and alias URLs, a webmaster can use Deme to create a completely customized site that has no sign of Deme (unless a visitor specifically types in a /item/ or /meta/ URL).
However, DjangoTemplateDocuments only allow the content to be customized, and not the things that a view does. For example, one cannot write a DjangoTemplateDocument to create a new record in the database, or to send out an email when visited, or more importantly, to do unauthorized things like execute UNIX commands.

Layouts
^^^^^^^
In the future, we might have custom layouts. Let's think about that.


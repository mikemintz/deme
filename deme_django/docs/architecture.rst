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
Below are the core item types and the role they play (see the full ontology at http://deme.stanford.edu/item/codegraph).

* **Item:** Item is item type that everything inherits from. It gives us a completely unique id across all items. It defines two user-editable fields (``name`` and ``description``) and six automatically generated fields (``id``, ``version_number``, ``item_type``, ``creator``, ``created_at``, and ``trashed``).

  * The ``name`` field is the friendly name to refer to the specific item: the title of a document or the preferred name of a person, and is the kind of name that would appear as the <title> of a webpage or the text of a link to that item. Currently, the name field cannot be blank (so that the viewer always has some text to display), but we are considering making it blank for items that don't need names (like Memberships) and having the viewer deal with possibly blank names.
  * The ``description`` field is a string field for metadata, that can be used for any purpose.
  * The ``id`` field is an automatically incrementing integer that gives a globally unique identifier for every item.
  * The ``version_number`` field is the latest version number.
  * The ``item_type`` field is the name of the actual item type at the lowest level in the inheritance graph.
  * The ``creator`` field is a pointer to the Agent that created the item.
  * The ``created_at`` field is the date and time the item was created.
  * The ``trashed`` field is true or false, depending on whether the item is trashed or not.

Agents and related item types

* **Agent:** This item type represents an agent that can "do" things. Often this will be a person (see the Person subclass), but actions can also be performed by other agents, such as bots and anonymous agents. Agents are unique in the following ways:
    
  * Agents can be assigned permissions
  * Agents show up in the creator and updater fields of other items
  * Agents can authenticate with Deme using AuthenticationMethods
  * Agents can be contacted via their ContactMethods
  * Agents can subscribe to other items with Subscriptions

  There is only one field defined by this item type, ``last_online_at``, which stores the date and time when the agent last accessed a viewer.

* **AnonymousAgent**: This item type is the agent that users of Deme authenticate as by default. Because every action must be associated with a responsible Agent (e.g., updating an item), we require that users are authenticated as some Agent at all times. So if a user never bothers logging in at the website, they will automatically be logged in as an AnonymousAgent, even if the website says "not logged in". There should be exactly one AnonymousAgent at all times.

  This item type does not define any new fields.

* **AuthenticationMethod**: This item type represents an Agent's credentials to login. For example, there might be a AuthenticationMethod representing my Facebook account, a AuthenticationMethod representing my WebAuth account, and a AuthenticationMethod representing my OpenID account. Rather than storing the login credentials directly in a particular Agent, we allow agents to have multiple authentication methods, so that they can login different ways. In theory, AuthenticationMethods can also be used to sync profile information through APIs. There are subclasses of AuthenticationMethod for each different way of authenticating.

  This item type defines one field, an ``agent`` pointer that points to the agent that is holds this authentication method.

* **PasswordAuthenticationMethod**: This is an AuthenticationMethod that allows a user to log on with a username and a password. The username must be unique across the entire Deme installation. The password field is formatted the same as in the User model of the Django admin app (algo$salt$hash), and is thus not stored in plain text.

  This item type defines four fields: ``username``, ``password``, ``password_question``, and ``password_answer`` (the last two can be used to reset the password and send it to the Agent via one of its ContactMethods).

* **Person**: A Person is an Agent that represents a person in real life. It defines four user-editable fields about the person's name: ``first_name``, ``middle_names``, ``last_name``, and ``suffix``.
 
* **ContactMethod**: A ContactMethod belongs to an Agent and contains details on how to contact them. ContactMethod is meant to be abstract, so developers should always create subclasses rather than creating raw ContactMethods.

  This item type defines one field, an ``agent`` pointer that points to the agent that is holds this contact method.

  Currently, the following concrete subclasses of ContactMethod are defined (with the fields in parentheses):

  * ``EmailContactMethod(email)``
  * ``PhoneContactMethod(phone)``
  * ``FaxContactMethod(fax)``
  * ``WebsiteContactMethod(url)``
  * ``AIMContactMethod(screen_name)``
  * ``AddressContactMethod(street1, street2, city, state, country, zip)``

* **Subscription**: A Subscription is a relationship between an Item and a ContactMethod, indicating that all comments on the item should be sent to the contact method as notifications. This item type defines the following fields:

  * The ``contact_method`` field is a pointer to the ContactMethod that is subscribed with this Subscription.
  * The ``item`` field is a pointer to the Item that is subscribed to with this Subscription.
  * The ``deep`` field is a boolean, such that when deep=true and the item is a Collection, all comments on all items in the collection (direct or indirect) will be sent in addition to comments on the collection itself.
  * The ``notify_text`` field is a boolean that signifies that TextComments are included in the subscription.
  * The ``notify_edit`` field is a boolean that signifies that EditComments, TrashComments, UntrashComments, AddMemberComments, and RemoveMemberComments are included in the subscription.

Collections and related item types

* **Collection**: A Collection is an Item that represents an unordered set of other items. Collections just use pointers from Memberships to represent their contents, so multiple Collections can point to the same contained items. Since Collections are just pointed to, they do not define any new fields.

  Collections "directly" contain items via Memberships, but they also "indirectly" contain items via chained Memberships. If Collection 1 directly contains Collection 2 which directly contains Item 3, then Collection 1 indirectly contains Item 3, even though there may be no explicit Membership item specifying the indirect relationship between Collection 1 and Item 3. (In the actual implementation, a special database table called RecursiveMembership is used to store all indirect membership tuples, but it does not inherit from Item.)

  It is possible for there to be circular memberships. Collection 1 might contain Collection 2 and Collection 2 might contain Collection 1. This will not cause any errors: it simply means that Collection 1 indirectly contains itself. It is even possible that Collection 1 *directly* contains itself via a Membership to itself.

* **Group**: A group is a collection of Agents. A group has a folio that is used for collaboration among members. THis item type does not define any new fields, since it just inherits from Collection and is pointed to by Folio.

* **Folio**: A folio is a special collection that belongs to a group. It has one field, the ``group`` pointer, which must be unique (no two folios can share a group).

* **Membership**: A Membership is a relationship between a collection and one of its items. It defines two fields, an ``item`` pointer and a ``collection`` pointer.

Documents

* **Document**: A Document is an Item that is meant can be a unit of collaborative work. Document is meant to be abstract, so developers should always create subclasses rather than creating raw Documents. This item type does not define any fields.

* **TextDocument**: A TextDocument is a Document that has a body that stores arbitrary text. This item type defines one field, ``body``, which is a free-form text field.

* **DjangoTemplateDocument**: This item type is a TextDocument that stores Django template code. It can display a fully customized page on Deme. This is primarily useful for customizing the layout of some or all pages, but it can also be used to make pages that can display content not possible in other Documents. This item type defines two new fields:

  * The ``layout`` field a pointer to another DjangoTemplateDocument that specifies the layout this template should be rendered in (i.e., this template inherits from the layout template in the Django templating system). This field can be null.
  * The ``override_default_layout`` field is a boolean specifying the behavior when the ``layout`` field is null. If this field is true and ``layout`` is null, this template will be rendered without inheriting from any other. If this field is false and ``layout`` is null, then this field will inherit from the default layout (which is defined by the current Site).

* **HtmlDocument**: An HtmlDocument is a TextDocument that renders its body as HTML. It uses the same ``body`` field as TextDocument, so it does not define any new fields.

* **FileDocument**: A FileDocument is a Document that stores a file on the filesystem (could be an MP3 or a Microsoft Word Document). It is intended for all binary data, which does not belong in a TextDocument (even though it is technically possible). Subclasses of FileDocument may be able to understand various file formats and add metadata and extra functionality. This item type defines one new field, ``datafile``, which represents the path on the server's filesystem to the actual file.

* **ImageDocument**: An ImageDocument is a FileDocument that stores an image. Right now, the only difference is that viewers know the file can be displayed as an image. Currently it does not define any new fields, but in the future, it may add metadata like EXIF data and thumbnails.

Annotations (Transclusions, Comments, and Excerpts)

* **Transclusion**: A Transclusion is an embedded reference from a location in a specific version of a TextDocument to another Item. This item type defines the following fields:

  * The ``from_item`` field is a pointer to the TextDocument that is transcluding the other item.
  * The ``from_item_version_number`` field is the version number of the TextDocument in which this Transclusion occurs.
  * The ``from_item_index`` field is a character offset into the body of the TextDocument where the transclusion occurs.
  * The ``to_item`` field is a pointer to the Item that is referenced by this Transclusion.

* **Comment**: A Comment is a unit of discussion about an Item. Each comment specifies the commented item and version number (in the ``item`` and ``item_version_number`` fields). Comment is meant to be abstract, so developers should always create subclasses rather than creating raw Comments. Currently, users can only create TextComments. All other Comment types are automatically generated by Deme in response to certain actions (such as edits and trashings).

  If somebody creates Item 1, someone creates Comment 2 about Item 2, and someone responds to Comment 2 with Comment 3, then one would say that Comment 3 is a *direct* comment on Comment 2, and Comment 3 is an *indirect* comment on Item 1. The Comment item type only stores information about direct comments, but behind the scenes, the RecursiveComment table (which does not inherit from Item) keeps track of all of the indirect commenting so that viewers can efficiently render entire threads.

* **TextComment**: A TextComment is a Comment and a TextDocument combined. It is currently the only form of user-generated comments. It defines no new fields.

* **EditComment**: An EditComment is a Comment that is automatically generated whenever an agent edits an item. The commented item is the item that was edited, and the commented item version number is the new version that was just generated (as opposed to the previous version number). It defines no new fields.

* **TrashComment**: A TrashComment is a Comment that is automatically generated whenever an agent trashes an item. The commented item is the item that was trashed, and the commented item version number is the latest version number at the time of the trashing. It defines no new fields.

* **UntrashComment**: An UntrashComment is a Comment that is automatically generated whenever an agent untrashes an item. The commented item is the item that was trashed, and the commented item version number is the latest version number at the time of the untrashing. It defines no new fields.

* **AddMemberComment**: An AddMemberComment is a Comment that is automatically generated whenever an item is added to a collection (via a creation or untrashing of a Membership). The commented item is the collection, and the commented item version number is the latest version number at the time of the add. The ``membership`` field points to the new Membership.

* **RemoveMemberComment**: A RemoveMemberComment is a Comment that is automatically generated whenever an item is removed from a collection (via a trashing of a Membership). The commented item is the collection, and the commented item version number is the latest version number at the time of the remove. The membership field points to the old Membership.

* **Excerpt**: An Excerpt is an Item that refers to a portion of another Item (or an external resource, such as a webpage). Excerpt is meant to be abstract, so developers should always create subclasses rather than creating raw Excerpts.

* **TextDocumentExcerpt**: A TextDocumentExcerpt refers to a contiguous region of text in a version of another TextDocument in Deme. The body field contains the excerpted region, and the following fields are introduced:
 
  * The ``text_document`` field is a pointer to the TextDocument being excerpted.
  * The ``text_document_version_number`` field is the version number of the TextDocument being excerpted.
  * The ``start_index`` field identifies the character position of the beginning of the region.
  * The ``length`` field identifies the length in characters of the region.

Viewer aliases

In order to allow vanity URLs (i.e., things other than ``/item/item/5``), we have a system of hierarchical URLs. In the future, we'll need to make sure URL aliases cannot start with /item/ (our base URL for viewers), /static/ (our base URL for static content like stylesheets), or /meta/ (our base URL for Deme framework things like authentication). Right now, if someone makes a vanity URL with one of those prefixes, you just cannot reach it (it does not shadow the important URLs).

TODO continue here

* **ViewerRequest:** A ViewerRequest is an Item that represents a particular action at a particular viewer (basically a URL, although its stored more explicitly). It specifies a viewer (just a string, since viewers are not Items), an action (like "view" or "edit"), an item that is referred to (or null for the entire collection), and a query_string if you want to pass parameters to the viewer.
* **Site:** A Site is a ViewerRequest that represents a logical website with URLs. A Site can have multiple SiteDomains, but ordinarily it would just have one (multiple domains are useful if you want to enable www.example.com and example.com). Multiple Sites on the same Deme installation share the same Items with the same unique ids, but they resolve URLs differently so each Site can have a different page for /mike. If you go to the base URL of a site (like http://example.com/), you see the ViewerRequest that this Site inherits from.
* **SiteDomain:** A SiteDomain is an Item that represents a hostname for a Site.
* **CustomUrl:** An CustomUrl is a ViewerRequest that represents a specific path. Each CustomUrl has a parent ViewerRequest (it will be the Site if this CustomUrl is the first path component) and a string for the path component. So when a user visits http://example.com/mike/is/great, Deme looks for an CustomUrl with name "great" with a parent with name "is" with a parent with name "mike" with a parent Site with a SiteDomain "example.com".

Misc item types

* **DemeSetting**: This item type stores global settings for the Deme installation. Each DemeSetting has a unique ``key`` field and an arbitrary ``value`` field. Since values are strings of limited size, settings that involve a lot of text (e.g., a default layout) should have a value pointing to an item that contains the data (e.g., the id of a document).


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


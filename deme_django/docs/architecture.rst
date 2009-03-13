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

There are two ways of deleting items: deactivating and destroying. Neither of these methods removes any rows from the database. Deactivating is recoverable (by reactivating), destroying is not. The user interface ensures that deactivating happens before destroying.

* **Deactivating:** If an agent deactivates an item, it sets the active field to false. An agent can recover the item by reactivating it, which sets the active field back to true. Each time this happens, the version does not change, but a DeactivateActionNotice or ReactivateActionNotice is automatically generated to log when the item was active. Inactive items can still be viewed and edited as normally. The major difference between an active and an inactive item is that when an item is inactive, it will not be returned as the result of queries (unless the query specifically requests inactive items). For example, when you look at the list of students in a class, it will only show students that are active with classmemberships that are active.
* **Destroying:** After an item is deactivated, you can permanently nullify all of its fields (and/or the fields in its versions) so that it is impossible to recover (but keep active=false). A DestroyActionNotice is automatically generated to log when the item was around.

  Our solution is as follows. We allow any field to have the special NULL value from SQL. The application (not the database) ensures that fields only take on these values when the item is destroyed, and never otherwise (I haven't finished making sure this happens yet). Thus, to destroy an item is to set every field to NULL, and set destroyed=True (and leave alone id, item_type, and active, version_number). Destroying an item also removes all permissions and versions of the item. After an item is destroyed, nobody can make changes (in particular, it cannot be reactivated or edited).
  
  Normally, having NULL values makes the code much more complex and prone to bugs, since the developer has to write a lot of checks for NULL. For example, to display the name of the creator of an item, the developer would have to write something like ``if (item.creator != NULL && item.creator.name != NULL) ...``. Since we already do all of this up-front error checking in the permission system (to ensure that the logged in agent has permission to view the creator of the item and the name of the creator), all we have to do is modify the permission code so that users cannot view fields (or take any actions) for destroyed items. So if an item's creator was destroyed, a simple viewer will just display the creator's name in the same way it would display something it does not have permission to view (a more advanced viewer could check to see if it was destroyed).

  It will also be possible to destroy specific versions of an item (not yet implemented). You can destroy any version except for the latest version (if you want to destroy the latest version, just edit the item to make a new version so that the version you want to destroy is now the second-latest). Destroying a version will permanently NULLify all fields in the version.

Things stored outside the database
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Not every bit of persistent data is stored in the database in item fields. Here are the exceptions so far:

* Uploaded files (like the files corresponding to FileDocuments) are stored on the filesystem in the static files folder so they can be stored more efficiently (databases are not good for binary data) and so they can be served quickly by the webserver without going through Deme. The FileDocument item type has a string field that represents to the path on the filesystem to the file.
* Item type definitions are stored as code, not in the database. The fact that Person is a subtype of Agent and defines the first_name field is inferred from the Deme code, and should not be read from the database. In the future, we are considering creating a "ItemTypes" table that stores one row per item type (the size would remain fixed as long as the code does not change), and this way, we could refer to item types (one good example is an admin might want to create a permission for another user to create new items of a specified type). This would also be a good place to store dynamic settings specific to each item type (like default permissions). Since the item type definitions are static, it seems like we never need this ability, and can always emulate it with more code.

Core item types
^^^^^^^^^^^^^^^
Below are the core item types and the role they play (see the full ontology at http://deme.stanford.edu/item/codegraph).

* **Item:** Item is item type that everything inherits from. It gives us a completely unique id across all items. It defines two user-editable fields (``name`` and ``description``) and six automatically generated fields (``id``, ``version_number``, ``item_type``, ``creator``, ``created_at``, ``active``, and ``destroyed``).

  * The ``name`` field is the friendly name to refer to the specific item: the title of a document or the preferred name of a person, and is the kind of name that would appear as the <title> of a webpage or the text of a link to that item. Currently, the name field cannot be blank (so that the viewer always has some text to display), but we are considering making it blank for items that don't need names (like Memberships) and having the viewer deal with possibly blank names.
  * The ``description`` field is a string field for metadata, which can be used for any purpose. Generally, the description is not considered part of the body of the item itself, but tells what the item is. The description for a budget document item might read, "This is the budget as drafted by the budget committee."
  * The ``id`` field is an automatically incrementing integer that gives a globally unique identifier for every item.
  * The ``version_number`` field is the latest version number.
  * The ``item_type`` field is the name of the actual item type at the lowest level in the inheritance graph.
  * The ``creator`` field is a pointer to the Agent that created the item.
  * The ``created_at`` field is the date and time the item was created.
  * The ``active`` field is true or false, depending on whether the item is active or not.
  * The ``destroyed`` field is true or false, depending on whether the item is destroyed or not.

Agents and related item types

* **Agent:** This item type represents an agent that can "do" things. Often this will be a person (see the Person subclass), but actions can also be performed by other agents, such as bots and anonymous agents. Agents are unique in the following ways:
    
  * Agents can be assigned permissions
  * Agents show up in the creator and updater fields of other items
  * Agents can authenticate with Deme using AuthenticationMethods
  * Agents can be contacted via their ContactMethods
  * Agents can subscribe to other items with Subscriptions

  There is only one field defined by this item type, ``last_online_at``, which stores the date and time when the agent last accessed a viewer.

* **AnonymousAgent:** This item type is the agent that users of Deme authenticate as by default. Because every action must be associated with a responsible Agent (e.g., updating an item), we require that users are authenticated as some Agent at all times. So if a user never bothers logging in at the website, they will automatically be logged in as an AnonymousAgent, even if the website says "not logged in". There should be exactly one AnonymousAgent at all times.

  This item type does not define any new fields.

* **GroupAgent:** This item type is an Agent that acts on behalf of an entire group. It can't do anything that other agents can't do. It's significance is just symbolic: by being associated with a group, the actions taken by the group agent are seen as collective action of the group members. In general, permission to login_as the group agent will be limited to powerful members of the group. There should be exactly one GroupAgent for every group.

  This item type defines one field, a unique ``group`` pointer that points to the group it represents.

* **AuthenticationMethod:** This item type represents an Agent's credentials to login. For example, there might be a AuthenticationMethod representing my Facebook account, a AuthenticationMethod representing my WebAuth account, and a AuthenticationMethod representing my OpenID account. Rather than storing the login credentials directly in a particular Agent, we allow agents to have multiple authentication methods, so that they can login different ways. In theory, AuthenticationMethods can also be used to sync profile information through APIs. There are subclasses of AuthenticationMethod for each different way of authenticating.

  This item type defines one field, an ``agent`` pointer that points to the agent that is holds this authentication method.

* **OpenidAuthenticationMethod:** This is an AuthenticationMethod that allows a user to log on with an OpenID. The openid url must be unique across the entire Deme installation. It defines only one new field, ``openid_url``, which is all that we need to represent the identity.

* **WebauthAuthenticationMethod:** This is an AuthenticationMethod that allows a user to log on with Stanford's WebAuth system. The username must be unique across the entire Deme installation.

* **PasswordAuthenticationMethod:** This is an AuthenticationMethod that allows a user to log on with a username and a password. The username must be unique across the entire Deme installation. The password field is formatted the same as in the User model of the Django admin app (algo$salt$hash), and is thus not stored in plain text.

  This item type defines four fields: ``username``, ``password``, ``password_question``, and ``password_answer`` (the last two can be used to reset the password and send it to the Agent via one of its ContactMethods).

* **Person:** A Person is an Agent that represents a person in real life. It defines four user-editable fields about the person's name: ``first_name``, ``middle_names``, ``last_name``, and ``suffix``.
 
* **ContactMethod:** A ContactMethod belongs to an Agent and contains details on how to contact them. ContactMethod is meant to be abstract, so developers should always create subclasses rather than creating raw ContactMethods.

  This item type defines one field, an ``agent`` pointer that points to the agent that is holds this contact method.

  Currently, the following concrete subclasses of ContactMethod are defined (with the fields in parentheses):

  * ``EmailContactMethod(email)``
  * ``PhoneContactMethod(phone)``
  * ``FaxContactMethod(fax)``
  * ``WebsiteContactMethod(url)``
  * ``AIMContactMethod(screen_name)``
  * ``AddressContactMethod(street1, street2, city, state, country, zip)``

* **Subscription:** A Subscription is a relationship between an Item and a ContactMethod, indicating that all action notices on the item should be sent to the contact method as notifications. This item type defines the following fields:

  * The ``contact_method`` field is a pointer to the ContactMethod that is subscribed with this Subscription.
  * The ``item`` field is a pointer to the Item that is subscribed to with this Subscription.
  * The ``deep`` field is a boolean, such that when deep=true and the item is a Collection, all action notices on all items in the collection (direct or indirect) will be sent in addition to action notices on the collection itself.

Collections and related item types

* **Collection:** A Collection is an Item that represents an unordered set of other items. Collections just use pointers from Memberships to represent their contents, so multiple Collections can point to the same contained items. Since Collections are just pointed to, they do not define any new fields.

  Collections "directly" contain items via Memberships, but they also "indirectly" contain items via chained Memberships. If Collection 1 directly contains Collection 2 which directly contains Item 3, then Collection 1 indirectly contains Item 3, even though there may be no explicit Membership item specifying the indirect relationship between Collection 1 and Item 3. (In the actual implementation, a special database table called RecursiveMembership is used to store all indirect membership tuples, but it does not inherit from Item.)

  It is possible for there to be circular memberships. Collection 1 might contain Collection 2 and Collection 2 might contain Collection 1. This will not cause any errors: it simply means that Collection 1 indirectly contains itself. It is even possible that Collection 1 *directly* contains itself via a Membership to itself.

* **Group:** A group is a collection of Agents. A group has a folio that is used for collaboration among members. THis item type does not define any new fields, since it just inherits from Collection and is pointed to by Folio.

* **Folio:** A folio is a special collection that belongs to a group. It has one field, the ``group`` pointer, which must be unique (no two folios can share a group).

* **Membership:** A Membership is a relationship between a collection and one of its items. It defines two fields, an ``item`` pointer and a ``collection`` pointer.

Documents

* **Document:** A Document is an Item that is meant can be a unit of collaborative work. Document is meant to be abstract, so developers should always create subclasses rather than creating raw Documents. This item type does not define any fields.

* **TextDocument:** A TextDocument is a Document that has a body that stores arbitrary text. This item type defines one field, ``body``, which is a free-form text field.

* **DjangoTemplateDocument:** This item type is a TextDocument that stores Django template code. It can display a fully customized page on Deme. This is primarily useful for customizing the layout of some or all pages, but it can also be used to make pages that can display content not possible in other Documents. This item type defines two new fields:

  * The ``layout`` field a pointer to another DjangoTemplateDocument that specifies the layout this template should be rendered in (i.e., this template inherits from the layout template in the Django templating system). This field can be null.
  * The ``override_default_layout`` field is a boolean specifying the behavior when the ``layout`` field is null. If this field is true and ``layout`` is null, this template will be rendered without inheriting from any other. If this field is false and ``layout`` is null, then this field will inherit from the default layout (which is defined by the current Site).

* **HtmlDocument:** An HtmlDocument is a TextDocument that renders its body as HTML. It uses the same ``body`` field as TextDocument, so it does not define any new fields.

* **FileDocument:** A FileDocument is a Document that stores a file on the filesystem (could be an MP3 or a Microsoft Word Document). It is intended for all binary data, which does not belong in a TextDocument (even though it is technically possible). Subclasses of FileDocument may be able to understand various file formats and add metadata and extra functionality. This item type defines one new field, ``datafile``, which represents the path on the server's filesystem to the actual file.

* **ImageDocument:** An ImageDocument is a FileDocument that stores an image. Right now, the only difference is that viewers know the file can be displayed as an image. Currently it does not define any new fields, but in the future, it may add metadata like EXIF data and thumbnails.

Annotations (Transclusions, Comments, and Excerpts)

* **Transclusion:** A Transclusion is an embedded reference from a location in a specific version of a TextDocument to another Item. This item type defines the following fields:

  * The ``from_item`` field is a pointer to the TextDocument that is transcluding the other item.
  * The ``from_item_version_number`` field is the version number of the TextDocument in which this Transclusion occurs.
  * The ``from_item_index`` field is a character offset into the body of the TextDocument where the transclusion occurs.
  * The ``to_item`` field is a pointer to the Item that is referenced by this Transclusion.

* **Comment:** A Comment is a unit of discussion about an Item. Each comment specifies the commented item and version number (in the ``item`` and ``item_version_number`` fields). Comment is meant to be abstract, so developers should always create subclasses rather than creating raw Comments. Currently, users can only create TextComments.

  If somebody creates Item 1, someone creates Comment 2 about Item 2, and someone responds to Comment 2 with Comment 3, then one would say that Comment 3 is a *direct* comment on Comment 2, and Comment 3 is an *indirect* comment on Item 1. The Comment item type only stores information about direct comments, but behind the scenes, the RecursiveComment table (which does not inherit from Item) keeps track of all of the indirect commenting so that viewers can efficiently render entire threads.

* **TextComment:** A TextComment is a Comment and a TextDocument combined. It is currently the only form of user-generated comments. It defines no new fields.

* **Excerpt:** An Excerpt is an Item that refers to a portion of another Item (or an external resource, such as a webpage). Excerpt is meant to be abstract, so developers should always create subclasses rather than creating raw Excerpts.

* **TextDocumentExcerpt:** A TextDocumentExcerpt refers to a contiguous region of text in a version of another TextDocument in Deme. The body field contains the excerpted region, and the following fields are introduced:
 
  * The ``text_document`` field is a pointer to the TextDocument being excerpted.
  * The ``text_document_version_number`` field is the version number of the TextDocument being excerpted.
  * The ``start_index`` field identifies the character position of the beginning of the region.
  * The ``length`` field identifies the length in characters of the region.

Viewer aliases

In order to allow vanity URLs (i.e., things other than ``/item/item/5``), we have a system of hierarchical URLs. In the future, we'll need to make sure URL aliases cannot start with /item/ (our base URL for viewers), /static/ (our base URL for static content like stylesheets), or /meta/ (our base URL for Deme framework things like authentication). Right now, if someone makes a vanity URL with one of those prefixes, you just cannot reach it (it does not shadow the important URLs).

* **ViewerRequest:** A ViewerRequest represents a particular action at a particular viewer (basically a URL, although its stored more explicitly). A ViewerRequest is supposed to be abstract, so users can only create Sites and CustomUrls. It specifies the following fields
  
  * A ``viewer`` (just a string, since viewers are not Items)
  * An ``action`` (like "view" or "edit")
  * An ``item`` that is referred to (or null for item type actions like "list" and "new")
  * A ``query_string`` if you want to pass parameters to the viewer
  * A ``format`` (like "html" or "json", for the viewer to know what output to render)
    
* **Site:** A Site is a ViewerRequest that represents a logical website with URLs. Multiple Sites on the same Deme installation share the same Items with the same unique ids, but they resolve URLs differently so each Site can have a different page for /mike. If you go to the base URL of a site (like http://example.com/), you see the ViewerRequest that this Site inherits from. This item type specifies the following fields:

  * The ``hostname`` field specifies the hostname of this site, so that the viewer can determine which site a visitor is currently at from the URL.
  * The ``default_layout`` field is a pointer to a DjangoTemplateDocument. Whenever a visitor is at a URL designated for this site, the template will be rendered under this layout. If this field is null, the Deme default layout (in ``cms/templates/default_layout.html``) will be used.


* **CustomUrl:** A CustomUrl is a ViewerRequest that represents a specific path.
    
  Each CustomUrl has a ``parent_url`` field pointing to the parent ViewerRequest (it will be the Site if this CustomUrl is the first path component) and a ``path`` field. So when a user visits http://example.com/abc/def, Deme looks for a CustomUrl with name "def" with a parent with name "abc" with a parent Site with hostname "example.com". In other words, we need to find something that looks like this::

    CustomUrl(name="def", parent_url=CustomUrl(name="abc", parent_url=Site(hostname="example.com")))

Misc item types

* **DemeSetting:** This item type stores global settings for the Deme installation. Each DemeSetting has a unique ``key`` field and an arbitrary ``value`` field. Since values are strings of limited size, settings that involve a lot of text (e.g., a default layout) should have a value pointing to an item that contains the data (e.g., the id of a document).


ActionNotices
^^^^^^^^^^^^^^
ActionNotices keep records of every action that occurs in Deme. ActionNotices are not items themselves, but they exist in the database and point to items.

Every ActionNotice keeps the following fields

* Item (the item that was acted upon)
* Item version number (the version of the item after the action took place)
* Creator (the agent who acted upon the item)
* Created at (the date/time that the action took place)
* Description (the optional user-entered description of the action -- for edits, this is like an "Edit Summary", but it applies to any action)

There are currently 6 types of ActionNotices: DeactivateActionNotices, ReactivateActionNotices, DestroyActionNotices, CreateActionNotices, EditActionNotices, and RelationNotices. The first 5 are self-explanatory: when an agent deactivates, reactivates, destroys, creates, or edits an item, this automatically generates an ActionNotice. None of these 5 ActionNotices define new fields. Although it seems like the CreateActionNotices and EditActionNotices should define fields to specify what changed, this information can be inferred from the item itself (and its revisions).

RelationActionNotices are more interesting: when an agent modifies an item (the *from* item) that points to another item (the *to* item), a RelationActionNotice is generated about the *to* item. These notices are only generated when the pointer changes, either from something else to the *to* item, or from the *to* item to something else. RelationActionNotices define new fields to specify the *from* item and its version at the time of the action, and the field in the *from* item that points to the *to* item.

A good example of a RelationActionNotice is a membership that points to a collection. If I'm viewing the ActionNotices for the collection, I will see a RelationActionNotice saying that at some date, some user set the membership to point to this collection. Or in other words, an item was added to this collection.

In order to view ActionNotices, an agent must have the ``view_action_notices`` permission with respect to the item. For RelationActionNotices, an agent must also have permission to view the pointing field in the *from* item.

If you are subscribed to an item (via the Subscription item type), and you have permission to view ActionNotices on that item, you will receive notifications by email every time an ActionNotice is generated.

The ActionNotices about an agent include ActionNotices whose ``creator`` field points to the agent, in addition to ActionNotices whose ``item`` field points to the agent. Thus, if you subscribe to an agent, you will get emails about things they do, in addition to things done to them. For this reason, RelationActionNotices are not generated for the ``creator`` field of an item, or else there would be redundant ActionNotices on the same item.

Permissions
^^^^^^^^^^^
Permissions define what actions Agents can and cannot do. Similar to ActionNotices, permissions are not items themselves, but they exist in the database and point to items (it used to be that permissions were items, but for simplicity and efficiency, we now keep them separate).

There are two major types of permissions: item permissions and global permissions. Item permissions specify an ability and an item (such as "can edit the name of document 123") and global permissions just specify a global ability (such as "can create new documents"). Each item type defines a abilities that are relevant to it. For simplicity in the explanation below, pretend that item permissions and global permissions are just a unified permission, where the ``item`` pointer of a global permission is a special "global" value, since almost everything but the ``item`` field is identical between the two. (In the actual implementation, they are separated into different tables for code simplicity and efficiency.)

For both global and item permissions, there are three levels: AgentPermissions, CollectionPermissions, and EveryonePermissions. Earlier levels override later levels, so if an EveryonePermission specifies that nobody can create documents, but an AgentPermission specifies that I can create documents, then the AgentPermission overrides the EveryonePermission and I am allowed to create documents.

* **AgentPermission:** An AgentPermission has an ``agent`` pointer, and ``item`` pointer (except in AgentGlobalPermissions), an ``ability`` string, and an ``is_allowed`` boolean. An AgentPermission specifies that the agent does (or does not) have the ability with respect to the item.
* **CollectionPermission:** A CollectionPermission has a ``collection`` pointer, and ``item`` pointer (except in CollectionGlobalPermissions), an ``ability`` string, and an ``is_allowed`` boolean. A CollectionPermission specifies that all agents in the collection do (or do not) have the ability with respect to the item.
* **EveryonePermission:** An EveryonePermission has an ``item`` pointer (except in EveryoneGlobalPermissions), an ``ability`` string, and an ``is_allowed`` boolean. An EveryonePermission specifies that all agents have (or don't have) the ability with respect to the item.

The agent has an ability if one of the following holds:

#. The agent was directly assigned a permission that contains this ability with is_allowed=True.

#. All of the following holds:

  #. A Collection that the agent is in (directly or indirectly) was assigned a permission that contains this ability with is_allowed=True.
  #. The agent was NOT directly assigned a permission that contains this ability with is_allowed=False.

#. All of the following holds:

  #. There is an everyone permission that contains this ability with is_allowed=True.
  #. NO Collection that the agent is in (directly or indirectly) was assigned a permission that contains this ability with is_allowed=False.
  #. The agent was NOT directly assigned a permission that contains this ability with is_allowed=False.

#. All of the following holds (this step is not used for GlobalPermissions since there is no item type):

  #. There is a DemeSetting set to "true" with the key "cms.default_permission.<ITEM_TYPE_NAME>.<ABILITY>" (without angle brackets around the item type name and ability).
  #. There is NO everyone permission that contains this ability with is_allowed=False.
  #. NO Collection that the agent is in (directly or indirectly) was assigned a permission that contains this ability with is_allowed=False.
  #. The agent was NOT directly assigned a permission that contains this ability with is_allowed=False.

Below is a list of all possible global abilities:

* ``create Agent``
* ``create Collection``
* ``create DjangoTemplateDocument``
* ``create FileDocument``
* ``create Group``
* ``create HtmlDocument``
* ``create ImageDocument``
* ``create Person``
* ``create Site``
* ``create TextDocument``
* ``create TextDocumentExcerpt``
* ``do_anything`` (Agents with this ability automatically have every single global ability and every item ability with respect to every item. If an agent has this global ability in the final calculation, this overrides any item abilities at any level. As a specific unusual example, if an agent has the global ``do_anything`` ability from an EveryonePermission, then giving him any item ability with is_allowed=False will have no effect.)

Below is a list of item types and the item abilities they introduce:


* Item

  * ``do_anything`` (Agents this ability with respect to an item automatically have every item ability for that item.)
  * ``comment_on`` (With this ability you can create comments *directly* on the item. There is no way to restrict agents from leaving *indirect* comments on an item, apart from ensuring that they don't have the ability to comment on any of the item's existing comments.)
  * ``delete`` (With this ability you can deactivate, reativate, or destroy the item.)
  * ``view name``
  * ``view description``
  * ``view creator``
  * ``view created_at``
  * ``edit name``
  * ``edit description``

* Agent

  * ``add_contact_method`` (With this ability you can create ContactMethods belonging to this Agent.)
  * ``add_authentication_method`` (With this ability you can create AuthenticationMethods belonging to this Agent.)
  * ``login_as`` (With this ability you can authenticate as this Agent.)
  * ``view last_online_at``

* GroupAgent

  * ``view group``

* AuthenticationMethod

  * ``view agent``

* OpenidAuthenticationMethod

  * ``view openid_url``

* WebauthAuthenticationMethod

  * ``view username``

* PasswordAuthenticationMethod

  * ``view username``
  * ``view password``
  * ``view password_question``
  * ``view password_answer``
  * ``edit username``
  * ``edit password``
  * ``edit password_question``
  * ``edit password_answer``

* Person

  * ``view first_name``
  * ``view middle_names``
  * ``view last_name``
  * ``view suffix``
  * ``edit first_name``
  * ``edit middle_names``
  * ``edit last_name``
  * ``edit suffix``

* ContactMethod

  * ``add_subscription`` (With this ability you can create Subscriptions belonging to this ContactMethod.)
  * ``view agent``

* EmailContactMethod

  * ``view email``
  * ``edit email``

* PhoneContactMethod

  * ``view phone``
  * ``edit phone``

* FaxContactMethod

  * ``view fax``
  * ``edit fax``

* WebsiteContactMethod

  * ``view url``
  * ``edit url``

* AIMContactMethod

  * ``view screen_name``
  * ``edit screen_name``

* AddressContactMethod

  * ``view street1``
  * ``view street2``
  * ``view city``
  * ``view state``
  * ``view country``
  * ``view zip``
  * ``edit street1``
  * ``edit street2``
  * ``edit city``
  * ``edit state``
  * ``edit country``
  * ``edit zip``

* Subscription

  * ``view contact_method``
  * ``view item``
  * ``view deep``
  * ``view notify_text``
  * ``view notify_edit``
  * ``edit deep``
  * ``edit notify_text``
  * ``edit notify_edit``

* Collection

  * ``modify_membership`` (With this ability you can add and remove Memberships pointing to this Collection.)
  * ``add_self`` (With this ability, you can add yourself as a member of this Collection.)
  * ``remove_self`` (With this ability, you can remove yourself as a member of this Collection.)

* Folio

  * ``view group``

* Membership

  * ``view item``
  * ``view collection``

* TextDocument

  * ``view body``
  * ``edit body``
  * ``add_transclusion`` (With this ability, you can add a transclusion with this TextDocument as the from_item.)

* DjangoTemplateDocument

  * ``view layout``
  * ``view override_default_layout``
  * ``edit layout``
  * ``edit override_default_layout``

* FileDocument

  * ``view datafile``
  * ``edit datafile``

* Transclusion

  * ``view from_item``
  * ``view from_item_version_number``
  * ``view from_item_index``
  * ``view to_item``
  * ``edit from_item_index``

* Comment

  * ``view item``
  * ``view item_version_number``

* TextDocumentExcerpt

  * ``view text_document``
  * ``view text_document_version_number``
  * ``view start_index``
  * ``view length``
  * ``edit text_document_version_number``
  * ``edit start_index``
  * ``edit length``

* ViewerRequest

  * ``add_sub_path`` (With this ability you can create ViewerRequests with this ViewerRequest as the parent_url.)
  * ``view aliased_item``
  * ``view viewer``
  * ``view action``
  * ``view query_string``
  * ``view format``
  * ``edit aliased_item``
  * ``edit viewer``
  * ``edit action``
  * ``edit query_string``
  * ``edit format``

* Site

  * ``view hostname``
  * ``edit hostname``
  * ``view default_layout``
  * ``edit default_layout``

* CustomUrl

  * ``view parent_url``
  * ``view path``

* DemeSetting

  * ``view key``
  * ``view value``
  * ``edit value``

In order to implement permissions, Deme takes the currently authenticated Agent (anonymous or not), and decides whether it has the required ability to complete the requested action (or display some part of the view). Abilities are not just checked before doing actions, but they can also be used to filter out items on database lookups. For example, if my viewer is supposed to display a list of items I am allowed to see (because I have the ``view name`` ability), it will need to use permissions to filter out inappropriate results.


Front-end (viewers)
-------------------

Overview
^^^^^^^^
A viewer is a Python class that processes browser or API requests. Any URL that starts with ``/item/`` is routed to a viewer (vanity URLs are also routed to viewers via ViewerRequests, but ``/static/`` URLs and invalid URLs are not). Each viewer defines the item type it can accept, and multiple viewers can accept the same item type (you could have ItemViewer and SuperItemViewer which both handle items). There should be a default viewer for every item type with the same name as the item type (in lowercase), and if there is none, then the default viewer of the superclass should be used. Viewers that handle item type X always handle items that are in subclasses of X.

URLs
^^^^
Our URLs are restful. Every URL defines a viewer, an action, a noun (or none for actions on the entire item type), a format, an optional parameters in the query string. Here are some example URLs:


* /item/item (item viewer, default "list" action, default "html" format)
* /item/person/new.xml (person viewer, new action, xml format)
* /item/person/1 (person viewer, default "show" action, person with id=1 is the noun, default "html" format)
* /item/person/1/edit.json?version=5 (same as above, but json format, edit action, and version 5)

Actions
^^^^^^^
Every viewer URL defines a set of actions it responds to. Actions are divided into two groups: those that take nouns (which are always item ids) called item actions, and those that do not take nouns called item type actions. In order to make URLs unambiguous, item ids must be numbers, and action names can only be letters (although we may later decide to allow other characters, such as underscores and dashes, or even numbers that do not appear at the beginning).

An action corresponds to a single Python function. If you visit /item/item/list, Deme will call the type_list method of the ItemViewer class. If you visit /item/person/5/show, Deme will call the item_show method of the PersonViewer class. Actions return the HTTP response to go back to the browser. Actions can call other actions from other viewers to embed views in other views (for example, the DocumentViewer could embed a view from the PersonViewer to show a little profile of the author at the top).

Nouns
^^^^^
Item actions take in a noun in the URL, which is the unique id of the item it acts upon. If viewers need more information (say I submitted a form that specified multiple people I wanted to add to a group), the data is passed in the query string or the HTTP post data, and the data required is up to the specific viewer. The only query string parameters that are reserved right now by convention are "version" (which specifies a specific version of the item the viewer is acting on) and "redirect" (which specifies the URL to return to after submitting the form on this page).

Formats
^^^^^^^
An additional parameter is passed in defining the response format, like HTML or XML. The default is HTML. Most viewers ignore this now, but it's easy to act upon it. We might add something where viewers have to register which formats they respond to, so that we can display error messages when you type the wrong format rather than ignoring it. Note that the format only specifies the response format. The request format (what the browser sends to the server) is always the same: all parameters encoded in the URL or the HTTP post data. We will only be using HTTP as the transport for viewers (although we can define things that accept emails and SSH and other protocols, they just won't be called viewers).

Authentication
^^^^^^^^^^^^^^
Whenever a visitor (or another web service or bot) is at an action of a viewer, he has an authenticated AuthenticationMethod, and through that AuthenticationMethod, is an Agent. If a visitor has not authenticated, they'll be using AnonymousAgent. We will support various ways of authenticating via the different subclasses of AuthenticationMethod.

DjangoTemplateDocuments
^^^^^^^^^^^^^^^^^^^^^^^
There is a DjangoTemplateDocument viewer right now, which accepts DjangoTemplateDocuments, and when viewed with the "render" action, it renders the DjangoTemplateDocument as HTML (or whatever format) straight back to the browser. This allows users to add web content that is not really tied to a viewer, so they can fully customize the user experience. By using DjangoTemplateDocuments and vanity URLs, a webmaster can use Deme to create a completely customized site that has no sign of Deme (unless a visitor specifically types in a /item/ or /static/ URL).

However, DjangoTemplateDocuments only allow the content to be customized, and not the things that a view does. For example, one cannot write a DjangoTemplateDocument to create a new record in the database, or to send out an email when visited, or more importantly, to do unauthorized things like execute UNIX commands.

Also, every HTML response from a viewer is rendered by inheriting from the default layout from the given site, so by modifying DjangoTemplateDocuments, one can change the look and feel of ordinary viewers to some extent.

Modules
-------

Modules are self-contained collections of item types and viewers (and arbitrary Django code) that can be imported into any Deme project. They work just like Django apps, except by virtue of being in the ``modules/`` directory they are registered into the Deme viewer framework. All of the item types discussed in this document are part of the Deme "core" (the ``cms/`` directory). Modules cannot generally override or change functionality of existing parts of code (so you cannot add a button to a page rendered by ItemViewer). They can only add new functionality.

Email integration
-----------------

As described in the section on Subscriptions, Deme will email notifications for every action notice made on items that are subscribed to (in the future we will support other ContactMethods, like sending SMS notifications). The communication also goes the other way: if someone responds to a notification email (or sends an email to the address corresponding to a particular item), that will become a comment on Deme.

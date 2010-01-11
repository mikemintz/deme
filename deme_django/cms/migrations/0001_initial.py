
from south.db import db
from django.db import models
from deme_django.cms.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'AIMContactMethodVersion'
        db.create_table('cms_aimcontactmethodversion', (
            ('contactmethodversion_ptr', orm['cms.AIMContactMethodVersion:contactmethodversion_ptr']),
            ('screen_name', orm['cms.AIMContactMethodVersion:screen_name']),
        ))
        db.send_create_signal('cms', ['AIMContactMethodVersion'])
        
        # Adding model 'Webpage'
        db.create_table('cms_webpage', (
            ('item_ptr', orm['cms.Webpage:item_ptr']),
            ('url', orm['cms.Webpage:url']),
        ))
        db.send_create_signal('cms', ['Webpage'])
        
        # Adding model 'AnonymousAgentVersion'
        db.create_table('cms_anonymousagentversion', (
            ('agentversion_ptr', orm['cms.AnonymousAgentVersion:agentversion_ptr']),
        ))
        db.send_create_signal('cms', ['AnonymousAgentVersion'])
        
        # Adding model 'TextDocumentExcerpt'
        db.create_table('cms_textdocumentexcerpt', (
            ('textdocument_ptr', orm['cms.TextDocumentExcerpt:textdocument_ptr']),
            ('excerpt_ptr', orm['cms.TextDocumentExcerpt:excerpt_ptr']),
            ('text_document', orm['cms.TextDocumentExcerpt:text_document']),
            ('text_document_version_number', orm['cms.TextDocumentExcerpt:text_document_version_number']),
            ('start_index', orm['cms.TextDocumentExcerpt:start_index']),
            ('length', orm['cms.TextDocumentExcerpt:length']),
        ))
        db.send_create_signal('cms', ['TextDocumentExcerpt'])
        
        # Adding model 'FileDocumentVersion'
        db.create_table('cms_filedocumentversion', (
            ('documentversion_ptr', orm['cms.FileDocumentVersion:documentversion_ptr']),
            ('datafile', orm['cms.FileDocumentVersion:datafile']),
        ))
        db.send_create_signal('cms', ['FileDocumentVersion'])
        
        # Adding model 'PersonVersion'
        db.create_table('cms_personversion', (
            ('agentversion_ptr', orm['cms.PersonVersion:agentversion_ptr']),
            ('first_name', orm['cms.PersonVersion:first_name']),
            ('middle_names', orm['cms.PersonVersion:middle_names']),
            ('last_name', orm['cms.PersonVersion:last_name']),
            ('suffix', orm['cms.PersonVersion:suffix']),
        ))
        db.send_create_signal('cms', ['PersonVersion'])
        
        # Adding model 'FolioVersion'
        db.create_table('cms_folioversion', (
            ('collectionversion_ptr', orm['cms.FolioVersion:collectionversion_ptr']),
        ))
        db.send_create_signal('cms', ['FolioVersion'])
        
        # Adding model 'PhoneContactMethodVersion'
        db.create_table('cms_phonecontactmethodversion', (
            ('contactmethodversion_ptr', orm['cms.PhoneContactMethodVersion:contactmethodversion_ptr']),
            ('phone', orm['cms.PhoneContactMethodVersion:phone']),
        ))
        db.send_create_signal('cms', ['PhoneContactMethodVersion'])
        
        # Adding model 'DemeSettingVersion'
        db.create_table('cms_demesettingversion', (
            ('itemversion_ptr', orm['cms.DemeSettingVersion:itemversion_ptr']),
            ('value', orm['cms.DemeSettingVersion:value']),
        ))
        db.send_create_signal('cms', ['DemeSettingVersion'])
        
        # Adding model 'HtmlDocumentVersion'
        db.create_table('cms_htmldocumentversion', (
            ('textdocumentversion_ptr', orm['cms.HtmlDocumentVersion:textdocumentversion_ptr']),
        ))
        db.send_create_signal('cms', ['HtmlDocumentVersion'])
        
        # Adding model 'Person'
        db.create_table('cms_person', (
            ('agent_ptr', orm['cms.Person:agent_ptr']),
            ('first_name', orm['cms.Person:first_name']),
            ('middle_names', orm['cms.Person:middle_names']),
            ('last_name', orm['cms.Person:last_name']),
            ('suffix', orm['cms.Person:suffix']),
        ))
        db.send_create_signal('cms', ['Person'])
        
        # Adding model 'CollectionVersion'
        db.create_table('cms_collectionversion', (
            ('itemversion_ptr', orm['cms.CollectionVersion:itemversion_ptr']),
        ))
        db.send_create_signal('cms', ['CollectionVersion'])
        
        # Adding model 'Collection'
        db.create_table('cms_collection', (
            ('item_ptr', orm['cms.Collection:item_ptr']),
        ))
        db.send_create_signal('cms', ['Collection'])
        
        # Adding model 'Folio'
        db.create_table('cms_folio', (
            ('collection_ptr', orm['cms.Folio:collection_ptr']),
            ('group', orm['cms.Folio:group']),
        ))
        db.send_create_signal('cms', ['Folio'])
        
        # Adding model 'CreateActionNotice'
        db.create_table('cms_createactionnotice', (
            ('actionnotice_ptr', orm['cms.CreateActionNotice:actionnotice_ptr']),
        ))
        db.send_create_signal('cms', ['CreateActionNotice'])
        
        # Adding model 'PhoneContactMethod'
        db.create_table('cms_phonecontactmethod', (
            ('contactmethod_ptr', orm['cms.PhoneContactMethod:contactmethod_ptr']),
            ('phone', orm['cms.PhoneContactMethod:phone']),
        ))
        db.send_create_signal('cms', ['PhoneContactMethod'])
        
        # Adding model 'TransclusionVersion'
        db.create_table('cms_transclusionversion', (
            ('itemversion_ptr', orm['cms.TransclusionVersion:itemversion_ptr']),
            ('from_item_index', orm['cms.TransclusionVersion:from_item_index']),
        ))
        db.send_create_signal('cms', ['TransclusionVersion'])
        
        # Adding model 'OneToAllPermission'
        db.create_table('cms_onetoallpermission', (
            ('id', orm['cms.OneToAllPermission:id']),
            ('ability', orm['cms.OneToAllPermission:ability']),
            ('is_allowed', orm['cms.OneToAllPermission:is_allowed']),
            ('source', orm['cms.OneToAllPermission:source']),
        ))
        db.send_create_signal('cms', ['OneToAllPermission'])
        
        # Adding model 'AllToSomePermission'
        db.create_table('cms_alltosomepermission', (
            ('id', orm['cms.AllToSomePermission:id']),
            ('ability', orm['cms.AllToSomePermission:ability']),
            ('is_allowed', orm['cms.AllToSomePermission:is_allowed']),
            ('target', orm['cms.AllToSomePermission:target']),
        ))
        db.send_create_signal('cms', ['AllToSomePermission'])
        
        # Adding model 'MembershipVersion'
        db.create_table('cms_membershipversion', (
            ('itemversion_ptr', orm['cms.MembershipVersion:itemversion_ptr']),
            ('permission_enabled', orm['cms.MembershipVersion:permission_enabled']),
        ))
        db.send_create_signal('cms', ['MembershipVersion'])
        
        # Adding model 'EditActionNotice'
        db.create_table('cms_editactionnotice', (
            ('actionnotice_ptr', orm['cms.EditActionNotice:actionnotice_ptr']),
        ))
        db.send_create_signal('cms', ['EditActionNotice'])
        
        # Adding model 'FaxContactMethodVersion'
        db.create_table('cms_faxcontactmethodversion', (
            ('contactmethodversion_ptr', orm['cms.FaxContactMethodVersion:contactmethodversion_ptr']),
            ('fax', orm['cms.FaxContactMethodVersion:fax']),
        ))
        db.send_create_signal('cms', ['FaxContactMethodVersion'])
        
        # Adding model 'EmailContactMethod'
        db.create_table('cms_emailcontactmethod', (
            ('contactmethod_ptr', orm['cms.EmailContactMethod:contactmethod_ptr']),
            ('email', orm['cms.EmailContactMethod:email']),
        ))
        db.send_create_signal('cms', ['EmailContactMethod'])
        
        # Adding model 'EmailContactMethodVersion'
        db.create_table('cms_emailcontactmethodversion', (
            ('contactmethodversion_ptr', orm['cms.EmailContactMethodVersion:contactmethodversion_ptr']),
            ('email', orm['cms.EmailContactMethodVersion:email']),
        ))
        db.send_create_signal('cms', ['EmailContactMethodVersion'])
        
        # Adding model 'TextComment'
        db.create_table('cms_textcomment', (
            ('comment_ptr', orm['cms.TextComment:comment_ptr']),
            ('textdocument_ptr', orm['cms.TextComment:textdocument_ptr']),
        ))
        db.send_create_signal('cms', ['TextComment'])
        
        # Adding model 'Transclusion'
        db.create_table('cms_transclusion', (
            ('item_ptr', orm['cms.Transclusion:item_ptr']),
            ('from_item', orm['cms.Transclusion:from_item']),
            ('from_item_version_number', orm['cms.Transclusion:from_item_version_number']),
            ('from_item_index', orm['cms.Transclusion:from_item_index']),
            ('to_item', orm['cms.Transclusion:to_item']),
        ))
        db.send_create_signal('cms', ['Transclusion'])
        
        # Adding model 'ItemVersion'
        db.create_table('cms_itemversion', (
            ('id', orm['cms.ItemVersion:id']),
            ('name', orm['cms.ItemVersion:name']),
            ('description', orm['cms.ItemVersion:description']),
            ('default_viewer', orm['cms.ItemVersion:default_viewer']),
            ('current_item', orm['cms.ItemVersion:current_item']),
            ('version_number', orm['cms.ItemVersion:version_number']),
        ))
        db.send_create_signal('cms', ['ItemVersion'])
        
        # Adding model 'AIMContactMethod'
        db.create_table('cms_aimcontactmethod', (
            ('contactmethod_ptr', orm['cms.AIMContactMethod:contactmethod_ptr']),
            ('screen_name', orm['cms.AIMContactMethod:screen_name']),
        ))
        db.send_create_signal('cms', ['AIMContactMethod'])
        
        # Adding model 'AuthenticationMethod'
        db.create_table('cms_authenticationmethod', (
            ('item_ptr', orm['cms.AuthenticationMethod:item_ptr']),
            ('agent', orm['cms.AuthenticationMethod:agent']),
        ))
        db.send_create_signal('cms', ['AuthenticationMethod'])
        
        # Adding model 'TextDocumentExcerptVersion'
        db.create_table('cms_textdocumentexcerptversion', (
            ('textdocumentversion_ptr', orm['cms.TextDocumentExcerptVersion:textdocumentversion_ptr']),
            ('excerptversion_ptr', orm['cms.TextDocumentExcerptVersion:excerptversion_ptr']),
            ('text_document_version_number', orm['cms.TextDocumentExcerptVersion:text_document_version_number']),
            ('start_index', orm['cms.TextDocumentExcerptVersion:start_index']),
            ('length', orm['cms.TextDocumentExcerptVersion:length']),
        ))
        db.send_create_signal('cms', ['TextDocumentExcerptVersion'])
        
        # Adding model 'FaxContactMethod'
        db.create_table('cms_faxcontactmethod', (
            ('contactmethod_ptr', orm['cms.FaxContactMethod:contactmethod_ptr']),
            ('fax', orm['cms.FaxContactMethod:fax']),
        ))
        db.send_create_signal('cms', ['FaxContactMethod'])
        
        # Adding model 'FileDocument'
        db.create_table('cms_filedocument', (
            ('document_ptr', orm['cms.FileDocument:document_ptr']),
            ('datafile', orm['cms.FileDocument:datafile']),
        ))
        db.send_create_signal('cms', ['FileDocument'])
        
        # Adding model 'DjangoTemplateDocument'
        db.create_table('cms_djangotemplatedocument', (
            ('textdocument_ptr', orm['cms.DjangoTemplateDocument:textdocument_ptr']),
            ('layout', orm['cms.DjangoTemplateDocument:layout']),
            ('override_default_layout', orm['cms.DjangoTemplateDocument:override_default_layout']),
        ))
        db.send_create_signal('cms', ['DjangoTemplateDocument'])
        
        # Adding model 'CustomUrlVersion'
        db.create_table('cms_customurlversion', (
            ('viewerrequestversion_ptr', orm['cms.CustomUrlVersion:viewerrequestversion_ptr']),
        ))
        db.send_create_signal('cms', ['CustomUrlVersion'])
        
        # Adding model 'ActionNotice'
        db.create_table('cms_actionnotice', (
            ('id', orm['cms.ActionNotice:id']),
            ('action_item', orm['cms.ActionNotice:action_item']),
            ('action_item_version_number', orm['cms.ActionNotice:action_item_version_number']),
            ('action_agent', orm['cms.ActionNotice:action_agent']),
            ('action_time', orm['cms.ActionNotice:action_time']),
            ('action_summary', orm['cms.ActionNotice:action_summary']),
        ))
        db.send_create_signal('cms', ['ActionNotice'])
        
        # Adding model 'Comment'
        db.create_table('cms_comment', (
            ('item_ptr', orm['cms.Comment:item_ptr']),
            ('item', orm['cms.Comment:item']),
            ('item_version_number', orm['cms.Comment:item_version_number']),
            ('from_contact_method', orm['cms.Comment:from_contact_method']),
        ))
        db.send_create_signal('cms', ['Comment'])
        
        # Adding model 'AddressContactMethod'
        db.create_table('cms_addresscontactmethod', (
            ('contactmethod_ptr', orm['cms.AddressContactMethod:contactmethod_ptr']),
            ('street1', orm['cms.AddressContactMethod:street1']),
            ('street2', orm['cms.AddressContactMethod:street2']),
            ('city', orm['cms.AddressContactMethod:city']),
            ('state', orm['cms.AddressContactMethod:state']),
            ('country', orm['cms.AddressContactMethod:country']),
            ('zip', orm['cms.AddressContactMethod:zip']),
        ))
        db.send_create_signal('cms', ['AddressContactMethod'])
        
        # Adding model 'DocumentVersion'
        db.create_table('cms_documentversion', (
            ('itemversion_ptr', orm['cms.DocumentVersion:itemversion_ptr']),
        ))
        db.send_create_signal('cms', ['DocumentVersion'])
        
        # Adding model 'ExcerptVersion'
        db.create_table('cms_excerptversion', (
            ('itemversion_ptr', orm['cms.ExcerptVersion:itemversion_ptr']),
        ))
        db.send_create_signal('cms', ['ExcerptVersion'])
        
        # Adding model 'TextDocumentVersion'
        db.create_table('cms_textdocumentversion', (
            ('documentversion_ptr', orm['cms.TextDocumentVersion:documentversion_ptr']),
            ('body', orm['cms.TextDocumentVersion:body']),
        ))
        db.send_create_signal('cms', ['TextDocumentVersion'])
        
        # Adding model 'CommentVersion'
        db.create_table('cms_commentversion', (
            ('itemversion_ptr', orm['cms.CommentVersion:itemversion_ptr']),
        ))
        db.send_create_signal('cms', ['CommentVersion'])
        
        # Adding model 'Agent'
        db.create_table('cms_agent', (
            ('item_ptr', orm['cms.Agent:item_ptr']),
            ('last_online_at', orm['cms.Agent:last_online_at']),
        ))
        db.send_create_signal('cms', ['Agent'])
        
        # Adding model 'SiteVersion'
        db.create_table('cms_siteversion', (
            ('viewerrequestversion_ptr', orm['cms.SiteVersion:viewerrequestversion_ptr']),
            ('hostname', orm['cms.SiteVersion:hostname']),
            ('default_layout', orm['cms.SiteVersion:default_layout']),
        ))
        db.send_create_signal('cms', ['SiteVersion'])
        
        # Adding model 'ReactivateActionNotice'
        db.create_table('cms_reactivateactionnotice', (
            ('actionnotice_ptr', orm['cms.ReactivateActionNotice:actionnotice_ptr']),
        ))
        db.send_create_signal('cms', ['ReactivateActionNotice'])
        
        # Adding model 'GroupVersion'
        db.create_table('cms_groupversion', (
            ('collectionversion_ptr', orm['cms.GroupVersion:collectionversion_ptr']),
        ))
        db.send_create_signal('cms', ['GroupVersion'])
        
        # Adding model 'ViewerRequest'
        db.create_table('cms_viewerrequest', (
            ('item_ptr', orm['cms.ViewerRequest:item_ptr']),
            ('viewer', orm['cms.ViewerRequest:viewer']),
            ('action', orm['cms.ViewerRequest:action']),
            ('aliased_item', orm['cms.ViewerRequest:aliased_item']),
            ('query_string', orm['cms.ViewerRequest:query_string']),
            ('format', orm['cms.ViewerRequest:format']),
        ))
        db.send_create_signal('cms', ['ViewerRequest'])
        
        # Adding model 'ContactMethodVersion'
        db.create_table('cms_contactmethodversion', (
            ('itemversion_ptr', orm['cms.ContactMethodVersion:itemversion_ptr']),
        ))
        db.send_create_signal('cms', ['ContactMethodVersion'])
        
        # Adding model 'Group'
        db.create_table('cms_group', (
            ('collection_ptr', orm['cms.Group:collection_ptr']),
        ))
        db.send_create_signal('cms', ['Group'])
        
        # Adding model 'DeactivateActionNotice'
        db.create_table('cms_deactivateactionnotice', (
            ('actionnotice_ptr', orm['cms.DeactivateActionNotice:actionnotice_ptr']),
        ))
        db.send_create_signal('cms', ['DeactivateActionNotice'])
        
        # Adding model 'SubscriptionVersion'
        db.create_table('cms_subscriptionversion', (
            ('itemversion_ptr', orm['cms.SubscriptionVersion:itemversion_ptr']),
            ('deep', orm['cms.SubscriptionVersion:deep']),
            ('subscribe_edit', orm['cms.SubscriptionVersion:subscribe_edit']),
            ('subscribe_delete', orm['cms.SubscriptionVersion:subscribe_delete']),
            ('subscribe_comments', orm['cms.SubscriptionVersion:subscribe_comments']),
            ('subscribe_relations', orm['cms.SubscriptionVersion:subscribe_relations']),
            ('subscribe_members', orm['cms.SubscriptionVersion:subscribe_members']),
        ))
        db.send_create_signal('cms', ['SubscriptionVersion'])
        
        # Adding model 'RecursiveMembership'
        db.create_table('cms_recursivemembership', (
            ('id', orm['cms.RecursiveMembership:id']),
            ('parent', orm['cms.RecursiveMembership:parent']),
            ('child', orm['cms.RecursiveMembership:child']),
            ('permission_enabled', orm['cms.RecursiveMembership:permission_enabled']),
        ))
        db.send_create_signal('cms', ['RecursiveMembership'])
        
        # Adding model 'ViewerRequestVersion'
        db.create_table('cms_viewerrequestversion', (
            ('itemversion_ptr', orm['cms.ViewerRequestVersion:itemversion_ptr']),
            ('viewer', orm['cms.ViewerRequestVersion:viewer']),
            ('action', orm['cms.ViewerRequestVersion:action']),
            ('aliased_item', orm['cms.ViewerRequestVersion:aliased_item']),
            ('query_string', orm['cms.ViewerRequestVersion:query_string']),
            ('format', orm['cms.ViewerRequestVersion:format']),
        ))
        db.send_create_signal('cms', ['ViewerRequestVersion'])
        
        # Adding model 'OneToOnePermission'
        db.create_table('cms_onetoonepermission', (
            ('id', orm['cms.OneToOnePermission:id']),
            ('ability', orm['cms.OneToOnePermission:ability']),
            ('is_allowed', orm['cms.OneToOnePermission:is_allowed']),
            ('source', orm['cms.OneToOnePermission:source']),
            ('target', orm['cms.OneToOnePermission:target']),
        ))
        db.send_create_signal('cms', ['OneToOnePermission'])
        
        # Adding model 'ContactMethod'
        db.create_table('cms_contactmethod', (
            ('item_ptr', orm['cms.ContactMethod:item_ptr']),
            ('agent', orm['cms.ContactMethod:agent']),
        ))
        db.send_create_signal('cms', ['ContactMethod'])
        
        # Adding model 'WebpageVersion'
        db.create_table('cms_webpageversion', (
            ('itemversion_ptr', orm['cms.WebpageVersion:itemversion_ptr']),
            ('url', orm['cms.WebpageVersion:url']),
        ))
        db.send_create_signal('cms', ['WebpageVersion'])
        
        # Adding model 'DestroyActionNotice'
        db.create_table('cms_destroyactionnotice', (
            ('actionnotice_ptr', orm['cms.DestroyActionNotice:actionnotice_ptr']),
        ))
        db.send_create_signal('cms', ['DestroyActionNotice'])
        
        # Adding model 'SomeToSomePermission'
        db.create_table('cms_sometosomepermission', (
            ('id', orm['cms.SomeToSomePermission:id']),
            ('ability', orm['cms.SomeToSomePermission:ability']),
            ('is_allowed', orm['cms.SomeToSomePermission:is_allowed']),
            ('source', orm['cms.SomeToSomePermission:source']),
            ('target', orm['cms.SomeToSomePermission:target']),
        ))
        db.send_create_signal('cms', ['SomeToSomePermission'])
        
        # Adding model 'WebsiteContactMethodVersion'
        db.create_table('cms_websitecontactmethodversion', (
            ('contactmethodversion_ptr', orm['cms.WebsiteContactMethodVersion:contactmethodversion_ptr']),
            ('url', orm['cms.WebsiteContactMethodVersion:url']),
        ))
        db.send_create_signal('cms', ['WebsiteContactMethodVersion'])
        
        # Adding model 'AgentVersion'
        db.create_table('cms_agentversion', (
            ('itemversion_ptr', orm['cms.AgentVersion:itemversion_ptr']),
        ))
        db.send_create_signal('cms', ['AgentVersion'])
        
        # Adding model 'AuthenticationMethodVersion'
        db.create_table('cms_authenticationmethodversion', (
            ('itemversion_ptr', orm['cms.AuthenticationMethodVersion:itemversion_ptr']),
        ))
        db.send_create_signal('cms', ['AuthenticationMethodVersion'])
        
        # Adding model 'Document'
        db.create_table('cms_document', (
            ('item_ptr', orm['cms.Document:item_ptr']),
        ))
        db.send_create_signal('cms', ['Document'])
        
        # Adding model 'RelationActionNotice'
        db.create_table('cms_relationactionnotice', (
            ('actionnotice_ptr', orm['cms.RelationActionNotice:actionnotice_ptr']),
            ('from_item', orm['cms.RelationActionNotice:from_item']),
            ('from_item_version_number', orm['cms.RelationActionNotice:from_item_version_number']),
            ('from_field_name', orm['cms.RelationActionNotice:from_field_name']),
            ('from_field_model', orm['cms.RelationActionNotice:from_field_model']),
            ('relation_added', orm['cms.RelationActionNotice:relation_added']),
        ))
        db.send_create_signal('cms', ['RelationActionNotice'])
        
        # Adding model 'RecursiveComment'
        db.create_table('cms_recursivecomment', (
            ('id', orm['cms.RecursiveComment:id']),
            ('parent', orm['cms.RecursiveComment:parent']),
            ('child', orm['cms.RecursiveComment:child']),
        ))
        db.send_create_signal('cms', ['RecursiveComment'])
        
        # Adding model 'GroupAgent'
        db.create_table('cms_groupagent', (
            ('agent_ptr', orm['cms.GroupAgent:agent_ptr']),
            ('group', orm['cms.GroupAgent:group']),
        ))
        db.send_create_signal('cms', ['GroupAgent'])
        
        # Adding model 'Membership'
        db.create_table('cms_membership', (
            ('item_ptr', orm['cms.Membership:item_ptr']),
            ('item', orm['cms.Membership:item']),
            ('collection', orm['cms.Membership:collection']),
            ('permission_enabled', orm['cms.Membership:permission_enabled']),
        ))
        db.send_create_signal('cms', ['Membership'])
        
        # Adding model 'Site'
        db.create_table('cms_site', (
            ('viewerrequest_ptr', orm['cms.Site:viewerrequest_ptr']),
            ('hostname', orm['cms.Site:hostname']),
            ('default_layout', orm['cms.Site:default_layout']),
        ))
        db.send_create_signal('cms', ['Site'])
        
        # Adding model 'DjangoTemplateDocumentVersion'
        db.create_table('cms_djangotemplatedocumentversion', (
            ('textdocumentversion_ptr', orm['cms.DjangoTemplateDocumentVersion:textdocumentversion_ptr']),
            ('layout', orm['cms.DjangoTemplateDocumentVersion:layout']),
            ('override_default_layout', orm['cms.DjangoTemplateDocumentVersion:override_default_layout']),
        ))
        db.send_create_signal('cms', ['DjangoTemplateDocumentVersion'])
        
        # Adding model 'AddressContactMethodVersion'
        db.create_table('cms_addresscontactmethodversion', (
            ('contactmethodversion_ptr', orm['cms.AddressContactMethodVersion:contactmethodversion_ptr']),
            ('street1', orm['cms.AddressContactMethodVersion:street1']),
            ('street2', orm['cms.AddressContactMethodVersion:street2']),
            ('city', orm['cms.AddressContactMethodVersion:city']),
            ('state', orm['cms.AddressContactMethodVersion:state']),
            ('country', orm['cms.AddressContactMethodVersion:country']),
            ('zip', orm['cms.AddressContactMethodVersion:zip']),
        ))
        db.send_create_signal('cms', ['AddressContactMethodVersion'])
        
        # Adding model 'SomeToAllPermission'
        db.create_table('cms_sometoallpermission', (
            ('id', orm['cms.SomeToAllPermission:id']),
            ('ability', orm['cms.SomeToAllPermission:ability']),
            ('is_allowed', orm['cms.SomeToAllPermission:is_allowed']),
            ('source', orm['cms.SomeToAllPermission:source']),
        ))
        db.send_create_signal('cms', ['SomeToAllPermission'])
        
        # Adding model 'DemeSetting'
        db.create_table('cms_demesetting', (
            ('item_ptr', orm['cms.DemeSetting:item_ptr']),
            ('key', orm['cms.DemeSetting:key']),
            ('value', orm['cms.DemeSetting:value']),
        ))
        db.send_create_signal('cms', ['DemeSetting'])
        
        # Adding model 'GroupAgentVersion'
        db.create_table('cms_groupagentversion', (
            ('agentversion_ptr', orm['cms.GroupAgentVersion:agentversion_ptr']),
        ))
        db.send_create_signal('cms', ['GroupAgentVersion'])
        
        # Adding model 'Excerpt'
        db.create_table('cms_excerpt', (
            ('item_ptr', orm['cms.Excerpt:item_ptr']),
        ))
        db.send_create_signal('cms', ['Excerpt'])
        
        # Adding model 'WebsiteContactMethod'
        db.create_table('cms_websitecontactmethod', (
            ('contactmethod_ptr', orm['cms.WebsiteContactMethod:contactmethod_ptr']),
            ('url', orm['cms.WebsiteContactMethod:url']),
        ))
        db.send_create_signal('cms', ['WebsiteContactMethod'])
        
        # Adding model 'AllToOnePermission'
        db.create_table('cms_alltoonepermission', (
            ('id', orm['cms.AllToOnePermission:id']),
            ('ability', orm['cms.AllToOnePermission:ability']),
            ('is_allowed', orm['cms.AllToOnePermission:is_allowed']),
            ('target', orm['cms.AllToOnePermission:target']),
        ))
        db.send_create_signal('cms', ['AllToOnePermission'])
        
        # Adding model 'SomeToOnePermission'
        db.create_table('cms_sometoonepermission', (
            ('id', orm['cms.SomeToOnePermission:id']),
            ('ability', orm['cms.SomeToOnePermission:ability']),
            ('is_allowed', orm['cms.SomeToOnePermission:is_allowed']),
            ('source', orm['cms.SomeToOnePermission:source']),
            ('target', orm['cms.SomeToOnePermission:target']),
        ))
        db.send_create_signal('cms', ['SomeToOnePermission'])
        
        # Adding model 'CustomUrl'
        db.create_table('cms_customurl', (
            ('viewerrequest_ptr', orm['cms.CustomUrl:viewerrequest_ptr']),
            ('parent_url', orm['cms.CustomUrl:parent_url']),
            ('path', orm['cms.CustomUrl:path']),
        ))
        db.send_create_signal('cms', ['CustomUrl'])
        
        # Adding model 'TextCommentVersion'
        db.create_table('cms_textcommentversion', (
            ('commentversion_ptr', orm['cms.TextCommentVersion:commentversion_ptr']),
            ('textdocumentversion_ptr', orm['cms.TextCommentVersion:textdocumentversion_ptr']),
        ))
        db.send_create_signal('cms', ['TextCommentVersion'])
        
        # Adding model 'AnonymousAgent'
        db.create_table('cms_anonymousagent', (
            ('agent_ptr', orm['cms.AnonymousAgent:agent_ptr']),
        ))
        db.send_create_signal('cms', ['AnonymousAgent'])
        
        # Adding model 'Subscription'
        db.create_table('cms_subscription', (
            ('item_ptr', orm['cms.Subscription:item_ptr']),
            ('contact_method', orm['cms.Subscription:contact_method']),
            ('item', orm['cms.Subscription:item']),
            ('deep', orm['cms.Subscription:deep']),
            ('subscribe_edit', orm['cms.Subscription:subscribe_edit']),
            ('subscribe_delete', orm['cms.Subscription:subscribe_delete']),
            ('subscribe_comments', orm['cms.Subscription:subscribe_comments']),
            ('subscribe_relations', orm['cms.Subscription:subscribe_relations']),
            ('subscribe_members', orm['cms.Subscription:subscribe_members']),
        ))
        db.send_create_signal('cms', ['Subscription'])
        
        # Adding model 'AllToAllPermission'
        db.create_table('cms_alltoallpermission', (
            ('id', orm['cms.AllToAllPermission:id']),
            ('ability', orm['cms.AllToAllPermission:ability']),
            ('is_allowed', orm['cms.AllToAllPermission:is_allowed']),
        ))
        db.send_create_signal('cms', ['AllToAllPermission'])
        
        # Adding model 'OneToSomePermission'
        db.create_table('cms_onetosomepermission', (
            ('id', orm['cms.OneToSomePermission:id']),
            ('ability', orm['cms.OneToSomePermission:ability']),
            ('is_allowed', orm['cms.OneToSomePermission:is_allowed']),
            ('source', orm['cms.OneToSomePermission:source']),
            ('target', orm['cms.OneToSomePermission:target']),
        ))
        db.send_create_signal('cms', ['OneToSomePermission'])
        
        # Adding model 'TextDocument'
        db.create_table('cms_textdocument', (
            ('document_ptr', orm['cms.TextDocument:document_ptr']),
            ('body', orm['cms.TextDocument:body']),
        ))
        db.send_create_signal('cms', ['TextDocument'])
        
        # Adding model 'Item'
        db.create_table('cms_item', (
            ('id', orm['cms.Item:id']),
            ('version_number', orm['cms.Item:version_number']),
            ('item_type_string', orm['cms.Item:item_type_string']),
            ('active', orm['cms.Item:active']),
            ('destroyed', orm['cms.Item:destroyed']),
            ('creator', orm['cms.Item:creator']),
            ('created_at', orm['cms.Item:created_at']),
            ('name', orm['cms.Item:name']),
            ('description', orm['cms.Item:description']),
            ('default_viewer', orm['cms.Item:default_viewer']),
        ))
        db.send_create_signal('cms', ['Item'])
        
        # Adding model 'HtmlDocument'
        db.create_table('cms_htmldocument', (
            ('textdocument_ptr', orm['cms.HtmlDocument:textdocument_ptr']),
        ))
        db.send_create_signal('cms', ['HtmlDocument'])
        
        # Adding ManyToManyField 'RecursiveMembership.child_memberships'
        db.create_table('cms_recursivemembership_child_memberships', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('recursivemembership', models.ForeignKey(orm.RecursiveMembership, null=False)),
            ('membership', models.ForeignKey(orm.Membership, null=False))
        ))
        
        # Creating unique_together for [ability, source] on OneToAllPermission.
        db.create_unique('cms_onetoallpermission', ['ability', 'source_id'])
        
        # Creating unique_together for [contact_method, item] on Subscription.
        db.create_unique('cms_subscription', ['contact_method_id', 'item_id'])
        
        # Creating unique_together for [ability, source, target] on SomeToSomePermission.
        db.create_unique('cms_sometosomepermission', ['ability', 'source_id', 'target_id'])
        
        # Creating unique_together for [ability, target] on AllToSomePermission.
        db.create_unique('cms_alltosomepermission', ['ability', 'target_id'])
        
        # Creating unique_together for [ability] on AllToAllPermission.
        db.create_unique('cms_alltoallpermission', ['ability'])
        
        # Creating unique_together for [current_item, version_number] on ItemVersion.
        db.create_unique('cms_itemversion', ['current_item_id', 'version_number'])
        
        # Creating unique_together for [ability, source, target] on SomeToOnePermission.
        db.create_unique('cms_sometoonepermission', ['ability', 'source_id', 'target_id'])
        
        # Creating unique_together for [ability, source, target] on OneToSomePermission.
        db.create_unique('cms_onetosomepermission', ['ability', 'source_id', 'target_id'])
        
        # Creating unique_together for [ability, target] on AllToOnePermission.
        db.create_unique('cms_alltoonepermission', ['ability', 'target_id'])
        
        # Creating unique_together for [item, collection] on Membership.
        db.create_unique('cms_membership', ['item_id', 'collection_id'])
        
        # Creating unique_together for [ability, source] on SomeToAllPermission.
        db.create_unique('cms_sometoallpermission', ['ability', 'source_id'])
        
        # Creating unique_together for [parent, child] on RecursiveMembership.
        db.create_unique('cms_recursivemembership', ['parent_id', 'child_id'])
        
        # Creating unique_together for [parent_url, path] on CustomUrl.
        db.create_unique('cms_customurl', ['parent_url_id', 'path'])
        
        # Creating unique_together for [ability, source, target] on OneToOnePermission.
        db.create_unique('cms_onetoonepermission', ['ability', 'source_id', 'target_id'])
        
        # Creating unique_together for [parent, child] on RecursiveComment.
        db.create_unique('cms_recursivecomment', ['parent_id', 'child_id'])
        
    
    
    def backwards(self, orm):
        
        # Deleting unique_together for [parent, child] on RecursiveComment.
        db.delete_unique('cms_recursivecomment', ['parent_id', 'child_id'])
        
        # Deleting unique_together for [ability, source, target] on OneToOnePermission.
        db.delete_unique('cms_onetoonepermission', ['ability', 'source_id', 'target_id'])
        
        # Deleting unique_together for [parent_url, path] on CustomUrl.
        db.delete_unique('cms_customurl', ['parent_url_id', 'path'])
        
        # Deleting unique_together for [parent, child] on RecursiveMembership.
        db.delete_unique('cms_recursivemembership', ['parent_id', 'child_id'])
        
        # Deleting unique_together for [ability, source] on SomeToAllPermission.
        db.delete_unique('cms_sometoallpermission', ['ability', 'source_id'])
        
        # Deleting unique_together for [item, collection] on Membership.
        db.delete_unique('cms_membership', ['item_id', 'collection_id'])
        
        # Deleting unique_together for [ability, target] on AllToOnePermission.
        db.delete_unique('cms_alltoonepermission', ['ability', 'target_id'])
        
        # Deleting unique_together for [ability, source, target] on OneToSomePermission.
        db.delete_unique('cms_onetosomepermission', ['ability', 'source_id', 'target_id'])
        
        # Deleting unique_together for [ability, source, target] on SomeToOnePermission.
        db.delete_unique('cms_sometoonepermission', ['ability', 'source_id', 'target_id'])
        
        # Deleting unique_together for [current_item, version_number] on ItemVersion.
        db.delete_unique('cms_itemversion', ['current_item_id', 'version_number'])
        
        # Deleting unique_together for [ability] on AllToAllPermission.
        db.delete_unique('cms_alltoallpermission', ['ability'])
        
        # Deleting unique_together for [ability, target] on AllToSomePermission.
        db.delete_unique('cms_alltosomepermission', ['ability', 'target_id'])
        
        # Deleting unique_together for [ability, source, target] on SomeToSomePermission.
        db.delete_unique('cms_sometosomepermission', ['ability', 'source_id', 'target_id'])
        
        # Deleting unique_together for [contact_method, item] on Subscription.
        db.delete_unique('cms_subscription', ['contact_method_id', 'item_id'])
        
        # Deleting unique_together for [ability, source] on OneToAllPermission.
        db.delete_unique('cms_onetoallpermission', ['ability', 'source_id'])
        
        # Deleting model 'AIMContactMethodVersion'
        db.delete_table('cms_aimcontactmethodversion')
        
        # Deleting model 'Webpage'
        db.delete_table('cms_webpage')
        
        # Deleting model 'AnonymousAgentVersion'
        db.delete_table('cms_anonymousagentversion')
        
        # Deleting model 'TextDocumentExcerpt'
        db.delete_table('cms_textdocumentexcerpt')
        
        # Deleting model 'FileDocumentVersion'
        db.delete_table('cms_filedocumentversion')
        
        # Deleting model 'PersonVersion'
        db.delete_table('cms_personversion')
        
        # Deleting model 'FolioVersion'
        db.delete_table('cms_folioversion')
        
        # Deleting model 'PhoneContactMethodVersion'
        db.delete_table('cms_phonecontactmethodversion')
        
        # Deleting model 'DemeSettingVersion'
        db.delete_table('cms_demesettingversion')
        
        # Deleting model 'HtmlDocumentVersion'
        db.delete_table('cms_htmldocumentversion')
        
        # Deleting model 'Person'
        db.delete_table('cms_person')
        
        # Deleting model 'CollectionVersion'
        db.delete_table('cms_collectionversion')
        
        # Deleting model 'Collection'
        db.delete_table('cms_collection')
        
        # Deleting model 'Folio'
        db.delete_table('cms_folio')
        
        # Deleting model 'CreateActionNotice'
        db.delete_table('cms_createactionnotice')
        
        # Deleting model 'PhoneContactMethod'
        db.delete_table('cms_phonecontactmethod')
        
        # Deleting model 'TransclusionVersion'
        db.delete_table('cms_transclusionversion')
        
        # Deleting model 'OneToAllPermission'
        db.delete_table('cms_onetoallpermission')
        
        # Deleting model 'AllToSomePermission'
        db.delete_table('cms_alltosomepermission')
        
        # Deleting model 'MembershipVersion'
        db.delete_table('cms_membershipversion')
        
        # Deleting model 'EditActionNotice'
        db.delete_table('cms_editactionnotice')
        
        # Deleting model 'FaxContactMethodVersion'
        db.delete_table('cms_faxcontactmethodversion')
        
        # Deleting model 'EmailContactMethod'
        db.delete_table('cms_emailcontactmethod')
        
        # Deleting model 'EmailContactMethodVersion'
        db.delete_table('cms_emailcontactmethodversion')
        
        # Deleting model 'TextComment'
        db.delete_table('cms_textcomment')
        
        # Deleting model 'Transclusion'
        db.delete_table('cms_transclusion')
        
        # Deleting model 'ItemVersion'
        db.delete_table('cms_itemversion')
        
        # Deleting model 'AIMContactMethod'
        db.delete_table('cms_aimcontactmethod')
        
        # Deleting model 'AuthenticationMethod'
        db.delete_table('cms_authenticationmethod')
        
        # Deleting model 'TextDocumentExcerptVersion'
        db.delete_table('cms_textdocumentexcerptversion')
        
        # Deleting model 'FaxContactMethod'
        db.delete_table('cms_faxcontactmethod')
        
        # Deleting model 'FileDocument'
        db.delete_table('cms_filedocument')
        
        # Deleting model 'DjangoTemplateDocument'
        db.delete_table('cms_djangotemplatedocument')
        
        # Deleting model 'CustomUrlVersion'
        db.delete_table('cms_customurlversion')
        
        # Deleting model 'ActionNotice'
        db.delete_table('cms_actionnotice')
        
        # Deleting model 'Comment'
        db.delete_table('cms_comment')
        
        # Deleting model 'AddressContactMethod'
        db.delete_table('cms_addresscontactmethod')
        
        # Deleting model 'DocumentVersion'
        db.delete_table('cms_documentversion')
        
        # Deleting model 'ExcerptVersion'
        db.delete_table('cms_excerptversion')
        
        # Deleting model 'TextDocumentVersion'
        db.delete_table('cms_textdocumentversion')
        
        # Deleting model 'CommentVersion'
        db.delete_table('cms_commentversion')
        
        # Deleting model 'Agent'
        db.delete_table('cms_agent')
        
        # Deleting model 'SiteVersion'
        db.delete_table('cms_siteversion')
        
        # Deleting model 'ReactivateActionNotice'
        db.delete_table('cms_reactivateactionnotice')
        
        # Deleting model 'GroupVersion'
        db.delete_table('cms_groupversion')
        
        # Deleting model 'ViewerRequest'
        db.delete_table('cms_viewerrequest')
        
        # Deleting model 'ContactMethodVersion'
        db.delete_table('cms_contactmethodversion')
        
        # Deleting model 'Group'
        db.delete_table('cms_group')
        
        # Deleting model 'DeactivateActionNotice'
        db.delete_table('cms_deactivateactionnotice')
        
        # Deleting model 'SubscriptionVersion'
        db.delete_table('cms_subscriptionversion')
        
        # Deleting model 'RecursiveMembership'
        db.delete_table('cms_recursivemembership')
        
        # Deleting model 'ViewerRequestVersion'
        db.delete_table('cms_viewerrequestversion')
        
        # Deleting model 'OneToOnePermission'
        db.delete_table('cms_onetoonepermission')
        
        # Deleting model 'ContactMethod'
        db.delete_table('cms_contactmethod')
        
        # Deleting model 'WebpageVersion'
        db.delete_table('cms_webpageversion')
        
        # Deleting model 'DestroyActionNotice'
        db.delete_table('cms_destroyactionnotice')
        
        # Deleting model 'SomeToSomePermission'
        db.delete_table('cms_sometosomepermission')
        
        # Deleting model 'WebsiteContactMethodVersion'
        db.delete_table('cms_websitecontactmethodversion')
        
        # Deleting model 'AgentVersion'
        db.delete_table('cms_agentversion')
        
        # Deleting model 'AuthenticationMethodVersion'
        db.delete_table('cms_authenticationmethodversion')
        
        # Deleting model 'Document'
        db.delete_table('cms_document')
        
        # Deleting model 'RelationActionNotice'
        db.delete_table('cms_relationactionnotice')
        
        # Deleting model 'RecursiveComment'
        db.delete_table('cms_recursivecomment')
        
        # Deleting model 'GroupAgent'
        db.delete_table('cms_groupagent')
        
        # Deleting model 'Membership'
        db.delete_table('cms_membership')
        
        # Deleting model 'Site'
        db.delete_table('cms_site')
        
        # Deleting model 'DjangoTemplateDocumentVersion'
        db.delete_table('cms_djangotemplatedocumentversion')
        
        # Deleting model 'AddressContactMethodVersion'
        db.delete_table('cms_addresscontactmethodversion')
        
        # Deleting model 'SomeToAllPermission'
        db.delete_table('cms_sometoallpermission')
        
        # Deleting model 'DemeSetting'
        db.delete_table('cms_demesetting')
        
        # Deleting model 'GroupAgentVersion'
        db.delete_table('cms_groupagentversion')
        
        # Deleting model 'Excerpt'
        db.delete_table('cms_excerpt')
        
        # Deleting model 'WebsiteContactMethod'
        db.delete_table('cms_websitecontactmethod')
        
        # Deleting model 'AllToOnePermission'
        db.delete_table('cms_alltoonepermission')
        
        # Deleting model 'SomeToOnePermission'
        db.delete_table('cms_sometoonepermission')
        
        # Deleting model 'CustomUrl'
        db.delete_table('cms_customurl')
        
        # Deleting model 'TextCommentVersion'
        db.delete_table('cms_textcommentversion')
        
        # Deleting model 'AnonymousAgent'
        db.delete_table('cms_anonymousagent')
        
        # Deleting model 'Subscription'
        db.delete_table('cms_subscription')
        
        # Deleting model 'AllToAllPermission'
        db.delete_table('cms_alltoallpermission')
        
        # Deleting model 'OneToSomePermission'
        db.delete_table('cms_onetosomepermission')
        
        # Deleting model 'TextDocument'
        db.delete_table('cms_textdocument')
        
        # Deleting model 'Item'
        db.delete_table('cms_item')
        
        # Deleting model 'HtmlDocument'
        db.delete_table('cms_htmldocument')
        
        # Dropping ManyToManyField 'RecursiveMembership.child_memberships'
        db.delete_table('cms_recursivemembership_child_memberships')
        
    
    
    models = {
        'cms.actionnotice': {
            'action_agent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'action_notices_created'", 'to': "orm['cms.Agent']"}),
            'action_item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'action_notices'", 'to': "orm['cms.Item']"}),
            'action_item_version_number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'action_summary': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'action_time': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'cms.addresscontactmethod': {
            'city': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'street1': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'street2': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'zip': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'cms.addresscontactmethodversion': {
            'city': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'street1': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'street2': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'zip': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'cms.agent': {
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'last_online_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        'cms.agentversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.aimcontactmethod': {
            'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'screen_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'})
        },
        'cms.aimcontactmethodversion': {
            'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'screen_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'})
        },
        'cms.alltoallpermission': {
            'Meta': {'unique_together': "(('ability',),)"},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'})
        },
        'cms.alltoonepermission': {
            'Meta': {'unique_together': "(('ability', 'target'),)"},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'all_to_one_permissions_as_target'", 'to': "orm['cms.Item']"})
        },
        'cms.alltosomepermission': {
            'Meta': {'unique_together': "(('ability', 'target'),)"},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'all_to_some_permissions_as_target'", 'to': "orm['cms.Collection']"})
        },
        'cms.anonymousagent': {
            'agent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Agent']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.anonymousagentversion': {
            'agentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.AgentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.authenticationmethod': {
            'agent': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'authentication_methods'", 'null': 'True', 'to': "orm['cms.Agent']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.authenticationmethodversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.collection': {
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.collectionversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.comment': {
            'from_contact_method': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'comments_from_contactmethod'", 'null': 'True', 'blank': 'True', 'to': "orm['cms.ContactMethod']"}),
            'item': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'comments'", 'null': 'True', 'to': "orm['cms.Item']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'item_version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'})
        },
        'cms.commentversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.contactmethod': {
            'agent': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'contact_methods'", 'null': 'True', 'to': "orm['cms.Agent']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.contactmethodversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.createactionnotice': {
            'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.customurl': {
            'Meta': {'unique_together': "(('parent_url', 'path'),)"},
            'parent_url': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'child_urls'", 'null': 'True', 'to': "orm['cms.ViewerRequest']"}),
            'path': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'viewerrequest_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ViewerRequest']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.customurlversion': {
            'viewerrequestversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ViewerRequestVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.deactivateactionnotice': {
            'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.demesetting': {
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'unique': 'True', 'null': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'cms.demesettingversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'cms.destroyactionnotice': {
            'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.djangotemplatedocument': {
            'layout': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'django_template_documents_with_layout'", 'null': 'True', 'blank': 'True', 'to': "orm['cms.DjangoTemplateDocument']"}),
            'override_default_layout': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True'}),
            'textdocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocument']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.djangotemplatedocumentversion': {
            'layout': ('django.db.models.ForeignKey', [], {'related_name': "'version_django_template_documents_with_layout'", 'default': 'None', 'to': "orm['cms.DjangoTemplateDocument']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'override_default_layout': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True'}),
            'textdocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.document': {
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.documentversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.editactionnotice': {
            'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.emailcontactmethod': {
            'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'default': "''", 'max_length': '320', 'null': 'True'})
        },
        'cms.emailcontactmethodversion': {
            'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'default': "''", 'max_length': '320', 'null': 'True'})
        },
        'cms.excerpt': {
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.excerptversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.faxcontactmethod': {
            'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'fax': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True'})
        },
        'cms.faxcontactmethodversion': {
            'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'fax': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True'})
        },
        'cms.filedocument': {
            'datafile': ('django.db.models.fields.files.FileField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Document']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.filedocumentversion': {
            'datafile': ('django.db.models.fields.files.FileField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'documentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.DocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.folio': {
            'collection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Collection']", 'unique': 'True', 'primary_key': 'True'}),
            'group': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'folios'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.Group']"})
        },
        'cms.folioversion': {
            'collectionversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CollectionVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.group': {
            'collection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Collection']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.groupagent': {
            'agent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Agent']", 'unique': 'True', 'primary_key': 'True'}),
            'group': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'group_agents'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.Group']"})
        },
        'cms.groupagentversion': {
            'agentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.AgentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.groupversion': {
            'collectionversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CollectionVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.htmldocument': {
            'textdocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocument']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.htmldocumentversion': {
            'textdocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.item': {
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)', 'null': 'True'}),
            'creator': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'items_created'", 'null': 'True', 'to': "orm['cms.Agent']"}),
            'default_viewer': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'destroyed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_type_string': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
        },
        'cms.itemversion': {
            'Meta': {'unique_together': "(('current_item', 'version_number'),)"},
            'current_item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'versions'", 'to': "orm['cms.Item']"}),
            'default_viewer': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'version_number': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'cms.membership': {
            'Meta': {'unique_together': "(('item', 'collection'),)"},
            'collection': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'child_memberships'", 'null': 'True', 'to': "orm['cms.Collection']"}),
            'item': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'memberships'", 'null': 'True', 'to': "orm['cms.Item']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'permission_enabled': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True'})
        },
        'cms.membershipversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'permission_enabled': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True'})
        },
        'cms.onetoallpermission': {
            'Meta': {'unique_together': "(('ability', 'source'),)"},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'one_to_all_permissions_as_source'", 'to': "orm['cms.Agent']"})
        },
        'cms.onetoonepermission': {
            'Meta': {'unique_together': "(('ability', 'source', 'target'),)"},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'one_to_one_permissions_as_source'", 'to': "orm['cms.Agent']"}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'one_to_one_permissions_as_target'", 'to': "orm['cms.Item']"})
        },
        'cms.onetosomepermission': {
            'Meta': {'unique_together': "(('ability', 'source', 'target'),)"},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'one_to_some_permissions_as_source'", 'to': "orm['cms.Agent']"}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'one_to_some_permissions_as_target'", 'to': "orm['cms.Collection']"})
        },
        'cms.person': {
            'agent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Agent']", 'unique': 'True', 'primary_key': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'middle_names': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'suffix': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'cms.personversion': {
            'agentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.AgentVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'middle_names': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'suffix': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'cms.phonecontactmethod': {
            'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True'})
        },
        'cms.phonecontactmethodversion': {
            'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True'})
        },
        'cms.reactivateactionnotice': {
            'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.recursivecomment': {
            'Meta': {'unique_together': "(('parent', 'child'),)"},
            'child': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recursive_comments_as_child'", 'to': "orm['cms.Comment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recursive_comments_as_parent'", 'to': "orm['cms.Item']"})
        },
        'cms.recursivemembership': {
            'Meta': {'unique_together': "(('parent', 'child'),)"},
            'child': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recursive_memberships_as_child'", 'to': "orm['cms.Item']"}),
            'child_memberships': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['cms.Membership']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recursive_memberships_as_parent'", 'to': "orm['cms.Collection']"}),
            'permission_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'cms.relationactionnotice': {
            'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'}),
            'from_field_model': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'from_field_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'from_item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'relation_action_notices_from'", 'to': "orm['cms.Item']"}),
            'from_item_version_number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'relation_added': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'cms.site': {
            'default_layout': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'sites_with_layout'", 'null': 'True', 'blank': 'True', 'to': "orm['cms.DjangoTemplateDocument']"}),
            'hostname': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'unique': 'True', 'null': 'True'}),
            'viewerrequest_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ViewerRequest']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.siteversion': {
            'default_layout': ('django.db.models.ForeignKey', [], {'related_name': "'version_sites_with_layout'", 'default': 'None', 'to': "orm['cms.DjangoTemplateDocument']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'hostname': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'viewerrequestversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ViewerRequestVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.sometoallpermission': {
            'Meta': {'unique_together': "(('ability', 'source'),)"},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'some_to_all_permissions_as_source'", 'to': "orm['cms.Collection']"})
        },
        'cms.sometoonepermission': {
            'Meta': {'unique_together': "(('ability', 'source', 'target'),)"},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'some_to_one_permissions_as_source'", 'to': "orm['cms.Collection']"}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'some_to_one_permissions_as_target'", 'to': "orm['cms.Item']"})
        },
        'cms.sometosomepermission': {
            'Meta': {'unique_together': "(('ability', 'source', 'target'),)"},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'some_to_some_permissions_as_source'", 'to': "orm['cms.Collection']"}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'some_to_some_permissions_as_target'", 'to': "orm['cms.Collection']"})
        },
        'cms.subscription': {
            'Meta': {'unique_together': "(('contact_method', 'item'),)"},
            'contact_method': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'subscriptions'", 'null': 'True', 'to': "orm['cms.ContactMethod']"}),
            'deep': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True'}),
            'item': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'subscriptions_to'", 'null': 'True', 'to': "orm['cms.Item']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'subscribe_comments': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True'}),
            'subscribe_delete': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True'}),
            'subscribe_edit': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True'}),
            'subscribe_members': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True'}),
            'subscribe_relations': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True'})
        },
        'cms.subscriptionversion': {
            'deep': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True'}),
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'subscribe_comments': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True'}),
            'subscribe_delete': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True'}),
            'subscribe_edit': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True'}),
            'subscribe_members': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True'}),
            'subscribe_relations': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True'})
        },
        'cms.textcomment': {
            'comment_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Comment']", 'unique': 'True'}),
            'textdocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocument']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.textcommentversion': {
            'commentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CommentVersion']", 'unique': 'True'}),
            'textdocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.textdocument': {
            'body': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Document']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.textdocumentexcerpt': {
            'excerpt_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Excerpt']", 'unique': 'True', 'primary_key': 'True'}),
            'length': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'start_index': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'text_document': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'text_document_excerpts'", 'null': 'True', 'to': "orm['cms.TextDocument']"}),
            'text_document_version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'textdocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocument']", 'unique': 'True'})
        },
        'cms.textdocumentexcerptversion': {
            'excerptversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ExcerptVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'length': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'start_index': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'text_document_version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'textdocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocumentVersion']", 'unique': 'True'})
        },
        'cms.textdocumentversion': {
            'body': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'documentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.DocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.transclusion': {
            'from_item': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'transclusions_from'", 'null': 'True', 'to': "orm['cms.TextDocument']"}),
            'from_item_index': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'from_item_version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'to_item': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'transclusions_to'", 'null': 'True', 'to': "orm['cms.Item']"})
        },
        'cms.transclusionversion': {
            'from_item_index': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.viewerrequest': {
            'action': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'aliased_item': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'viewer_requests'", 'null': 'True', 'blank': 'True', 'to': "orm['cms.Item']"}),
            'format': ('django.db.models.fields.CharField', [], {'default': "'html'", 'max_length': '255', 'null': 'True'}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'query_string': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'viewer': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'})
        },
        'cms.viewerrequestversion': {
            'action': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'aliased_item': ('django.db.models.ForeignKey', [], {'related_name': "'version_viewer_requests'", 'default': 'None', 'to': "orm['cms.Item']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'format': ('django.db.models.fields.CharField', [], {'default': "'html'", 'max_length': '255', 'null': 'True'}),
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'query_string': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'viewer': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'})
        },
        'cms.webpage': {
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'default': "'http://'", 'max_length': '255', 'null': 'True'})
        },
        'cms.webpageversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'default': "'http://'", 'max_length': '255', 'null': 'True'})
        },
        'cms.websitecontactmethod': {
            'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'default': "'http://'", 'max_length': '255', 'null': 'True'})
        },
        'cms.websitecontactmethodversion': {
            'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'default': "'http://'", 'max_length': '255', 'null': 'True'})
        }
    }
    
    complete_apps = ['cms']

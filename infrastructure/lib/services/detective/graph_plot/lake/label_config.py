# TODO: move to persistent store

from store.block_state import *

LABEL_NORMALIZE_MAP = {}

# Zoho
LABEL_NORMALIZE_MAP.update({
    'incremental_accounts_zoho_crm_stream': ACCOUNT_BLOCK_LABEL, 
    'incremental_activities_zoho_crm_stream': ACTIVITY_BLOCK_LABEL, 
    'incremental_calls_zoho_crm_stream': CALL_BLOCK_LABEL, 
    'incremental_contacts_zoho_crm_stream': CONTACT_BLOCK_LABEL, 
    'incremental_deals_zoho_crm_stream': DEAL_BLOCK_LABEL, 
    'incremental_events_zoho_crm_stream': EVENT_BLOCK_LABEL, 
    'incremental_leads_zoho_crm_stream': LEAD_BLOCK_LABEL, 
    'incremental_notes_zoho_crm_stream': COMMENT_BLOCK_LABEL, 
    'incremental_tasks_zoho_crm_stream': TASK_BLOCK_LABEL
})
 
# Zendesk
LABEL_NORMALIZE_MAP.update({
    'ticket_comments': COMMENT_BLOCK_LABEL,
    'tickets': TICKET_BLOCK_LABEL,
    'users': USER_BLOCK_LABEL,
    'organizations': ORGANIZATION_BLOCK_LABEL,
    'groups': GROUP_BLOCK_LABEL,
    'ticket_metrics': METRIC_BLOCK_LABEL,
    'brands': BRAND_BLOCK_LABEL,
})

# Slack
LABEL_NORMALIZE_MAP.update({
    'channels': CHANNEL_BLOCK_LABEL,
    'channel_messages': MESSAGE_BLOCK_LABEL,
    'users': USER_BLOCK_LABEL,
})

# Salesforce
LABEL_NORMALIZE_MAP.update({
    'Account': ACCOUNT_BLOCK_LABEL,
})

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
    'incremental_notes_zoho_crm_stream': NOTE_BLOCK_LABEL, 
    'incremental_tasks_zoho_crm_stream': TASK_BLOCK_LABEL
})
 
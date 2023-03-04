from app.chat.get import handler as chatget
from app.chat.post import handler as chatpost
from app.integration.get import handler as integrationget
from app.integration.post import handler as integrationpost
from app.item.get import handler as itemget
from app.item.post import handler as itempost


def unknown(event, context):
    print(event)
    print(context)
    return {
        'statusCode': 404,
        'body': 'Unknown endpoint'
    }

def chat_get(event, context):
    return chatget(event, context)

def chat_post(event, context):
    return chatpost(event, context)

def integration_get(event, context):
    return integrationget(event, context)

def integration_post(event, context):
    return integrationpost(event, context)

def item_get(event, context):
    return itemget(event, context)

def item_post(event, context):
    return itempost(event, context)
def unknown(event, context):
    print(event)
    print(context)
    return {
        'statusCode': 404,
        'body': 'Unknown endpoint'
    }

def chat_get(event, context):
    from app.api.chat.get import handler
    return handler(event, context)

def chat_post(event, context):
    from app.api.chat.post import handler
    return handler(event, context)

def integration_get(event, context):
    from app.api.integration.get import handler
    return handler(event, context)

def integration_post(event, context):
    from app.api.integration.post import handler
    return handler(event, context)

def item_get(event, context):
    from app.api.item.get import handler
    return handler(event, context)

def item_post(event, context):
    from app.api.item.post import handler
    return handler(event, context)

def mysterybox_post(event, context):
    from app.api.mysterybox.post import handler
    return handler(event, context)
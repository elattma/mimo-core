def unknown(event, context):
    print(event)
    print(context)
    return {
        'statusCode': 404,
        'body': 'Unknown endpoint'
    }

def chat_get(event, context):
    from app.chat.get import handler
    return handler(event, context)

def chat_post(event, context):
    from app.chat.post import handler
    return handler(event, context)

def integration_get(event, context):
    from app.integration.get import handler
    return handler(event, context)

def integration_post(event, context):
    from app.integration.post import handler
    return handler(event, context)

def item_get(event, context):
    from app.item.get import handler
    return handler(event, context)

def item_post(event, context):
    from app.item.post import handler
    return handler(event, context)

def blackbox_post(event, context):
    from app.blackbox.post import handler
    return handler(event, context)
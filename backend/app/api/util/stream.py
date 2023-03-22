import json

import requests


def send_chat(appsync_endpoint: str, authorization: str, user_id: str, input_chat_id: str, output_chat_id: str, message: str, role: str, timestamp: int, is_progress: bool = False) -> None:
    if not message:
        return

    query = 'mutation($input: ChatInput!) { proxyChat(input: $input) { userId, inputChatId, outputChatId, message, is_progress, role, timestamp }}'
    variables = json.dumps({
        "input": {
            "userId": user_id,
            "inputChatId": input_chat_id,
            "outputChatId": output_chat_id,
            "message": message,
            "is_progress": is_progress,
            "role": role,
            "timestamp": timestamp
        }
    })
    response = requests.post(
        appsync_endpoint,
        headers={
            'Authorization': authorization.replace('Bearer ', '')
        },
        data=json.dumps({
            'query': query,
            'variables': variables
        })
    )
    appsync_response = response.json()
    print(appsync_response)
import time

import requests
from db.pc import ParentChildDB, UserIntegrationItem


def refresh_token(db: ParentChildDB, client_id: str, client_secret: str, item: UserIntegrationItem):
    if not db or not item or not item.access_token:
        return None

    if not item.expiry_timestamp or int(time.time()) < item.expiry_timestamp or not item.refresh_token:
        return item.access_token

    if item.get_raw_child() == 'google':
        response = requests.post(
            "https://oauth2.googleapis.com/token", 
            data={
                'grant_type': 'refresh_token',
                'refresh_token': item.refresh_token,
                'client_id': client_id,
                'client_secret': client_secret
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            auth=(client_id, client_secret)
        )

        print(response)
        auth_response = response.json()
        print(auth_response)

        if not response or not auth_response or not auth_response['access_token']:
            return None
        
        access_token = auth_response['access_token']
        expiry_timestamp = auth_response['expires_in'] + int(time.time())

        db.write([UserIntegrationItem(item.parent, item.child, access_token=access_token, refresh_token=item.refresh_token, timestamp=item.timestamp, expiry_timestamp=expiry_timestamp)])

        return access_token

    return None

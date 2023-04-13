import re

from slack_bolt.app.app import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

SLACK_APP_TOKEN = ''
SLACK_BOT_TOKEN = ''
FAKE_LINK = ''
FAKE_RECIPIENT = ''
FAKE_SUBJECT = ''
FAKE_BODY = ''

app = App(token=SLACK_BOT_TOKEN, name='Email Agent')

@app.message(re.compile('(?s).*'))
def respond(message, say):
    channel_type = message['channel_type']
    if channel_type != 'im':
        return
    
    text = message['text']
    dm_channel = message['channel']

    blocks = [
        {
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": f"*To*: {FAKE_RECIPIENT}"
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": f"*Subject*: {FAKE_SUBJECT}"
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": f"{FAKE_BODY}"
			}
		},
		{
			'type': 'section',
			'text': {
				'type': 'mrkdwn',
				'text': 'I created a prepopulated email for you. Click the button to open it.'
			},
			'accessory': {
				'type': 'button',
				'text': {
					'type': 'plain_text',
					'text': 'Open'
				},
				'value': 'open_email',
				'url': FAKE_LINK,
				'action_id': 'open_email'
			}
		}
	]
    say(blocks=blocks, channel=dm_channel)

def main():
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()

if __name__ == '__main__':
    main()
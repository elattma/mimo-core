import re
from abc import ABC
from dataclasses import dataclass
from urllib.parse import quote

class EmailSystemResponse(ABC):
    @classmethod
    def from_agent_output(self, agent_output: str) -> 'EmailSystemResponse':
        '''Parses the agents output to get the components of the email and
        format them into a mailto: link.'''
        try:
            recipient_match = re.search(r'To:(.*)', agent_output)
            recipient = recipient_match.group(1).strip() if recipient_match else None
            subject_match = re.search(r'Subject:(.*)', agent_output)
            subject = subject_match.group(1).strip() if subject_match else None
            body_match = re.search(r'Subject:.*\n([\s\S]*)', agent_output)
            body = body_match.group(1).strip() if body_match else None
            link = 'mailto:'
            if recipient:
                link += quote(recipient)
            link += '?'
            if subject:
                link += f'subject={quote(subject)}'
            if body:
                if subject:
                    link += '&'
                link += f'body={quote(body)}'
            return EmailSystemSuccess(recipient, subject, body, link)
        except:
            return EmailSystemError('Failed to parse agent\'s output.')

@dataclass
class EmailSystemSuccess(EmailSystemResponse):
    recipient: str
    subject: str
    body: str
    link: str

@dataclass
class EmailSystemError(EmailSystemResponse):
    message: str
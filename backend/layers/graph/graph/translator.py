from typing import List

from graph.neo4j_ import Document

from .blocks import (BlockStream, BodyBlock, CommentBlock, ContactBlock,
                     DealBlock, MemberBlock, SummaryBlock, TitleBlock)

SUPPORTED_BLOCK_LABELS = set([
    SummaryBlock._LABEL,
    BodyBlock._LABEL,
    MemberBlock._LABEL,
    TitleBlock._LABEL,
    CommentBlock._LABEL,
    DealBlock._LABEL,
    ContactBlock._LABEL
])


class Translator:
    def __init__(self) -> None:
        pass

    @staticmethod
    def translate_document(integration: str, block_streams: List[BlockStream]) -> str:
        if not (integration and block_streams):
            return None
        if integration == 'google_mail':
            return Translator._translate_email(block_streams)

    @staticmethod
    def _translate_email(block_streams: List[BlockStream]) -> str:
        translation = 'EMAIL:\n'
        blocks = _get_sorted_blocks(block_streams)
        if 'title' in blocks and blocks['title']:
            title = Translator._translate_title_blocks(blocks['title'])
            translation += f'Title: {title}\n'
        if 'summary' in blocks and blocks['summary']:
            summary = Translator._translate_summary_blocks(blocks['summary'])
            translation += f'Summary:\n{summary}\n'
        if 'member' in blocks and blocks['member']:
            members = Translator._translate_member_blocks(blocks['member'])
            translation += f'Members:\n{members}\n'
        if 'body' in blocks and blocks['body']:
            body = Translator._translate_body_blocks(blocks['body'])
            translation += f'Body:\n{body}\n'
        return translation

    @staticmethod
    def _translate_account(account: Document) -> str:
        ...

    @staticmethod
    def _translate_text_document(account: Document) -> str:
        ...

    @staticmethod
    def _translate_ticket(ticket: Document) -> str:
        ...

    @staticmethod
    def translate_block_streams(block_streams: List[BlockStream]) -> str:
        if not block_streams:
            return None

        translated = []
        for block_stream in block_streams:
            if not (block_stream and block_stream.blocks and block_stream.label and block_stream.label in SUPPORTED_BLOCK_LABELS):
                print('invalid block stream!')
                continue

            if block_stream.label == SummaryBlock._LABEL:
                translated.append(
                    Translator._translate_summary_blocks(block_stream.blocks))
            elif block_stream.label == BodyBlock._LABEL:
                translated.append(
                    Translator._translate_body_blocks(block_stream.blocks))
            elif block_stream.label == MemberBlock._LABEL:
                translated.append(
                    Translator._translate_member_blocks(block_stream.blocks))
            elif block_stream.label == TitleBlock._LABEL:
                translated.append(
                    Translator._translate_title_blocks(block_stream.blocks))
            elif block_stream.label == CommentBlock._LABEL:
                translated.append(
                    Translator._translate_comment_blocks(block_stream.blocks))
            elif block_stream.label == DealBlock._LABEL:
                translated.append(
                    Translator._translate_deal_blocks(block_stream.blocks))
            elif block_stream.label == ContactBlock._LABEL:
                translated.append(
                    Translator._translate_contact_blocks(block_stream.blocks))

        return '\n\n'.join(translated) if translated else None

    @staticmethod
    def _translate_summary_blocks(summary_blocks: List[SummaryBlock]):
        summaries = []
        counter = 1
        for summary_block in summary_blocks:
            summaries.append(f'{counter}. {summary_block.text}')
            counter += 1
        summary = '\n'.join(summaries)
        return f'Page\'s summary is:\n"{summary}"'

    @staticmethod
    def _translate_body_blocks(body_blocks: List[BodyBlock]):
        bodies = []
        counter = 1
        for body_block in body_blocks:
            bodies.append(f'{counter}. {body_block.text}')
            counter += 1
        body = '\n'.join(bodies)
        return f'Page\'s body content includes:\n"{body}"'

    @staticmethod
    def _translate_member_blocks(member_blocks: List[MemberBlock]):
        members = []
        counter = 1
        for member_block in member_blocks:
            members.append(
                f'{counter}. {member_block.name} is a {member_block.relation.value}')
            counter += 1
        members = '\n'.join(members)
        return f'Page\'s members include:\n"{members}"'

    @staticmethod
    def _translate_title_blocks(title_blocks: List[TitleBlock]):
        titles = []
        counter = 1
        for title_block in title_blocks:
            titles.append(f'{counter}. {title_block.text}')
            counter += 1
        titles = '\n'.join(titles)
        return f'Page\'s titles include:\n"{titles}"'

    @staticmethod
    def _translate_comment_blocks(comment_blocks: List[CommentBlock]):
        comments = []
        counter = 1
        for comment_block in comment_blocks:
            comments.append(
                f'{counter}. {comment_block.author} said:\n"{comment_block.text}"')
            counter += 1
        comments = '\n'.join(comments)
        return f'Page\'s comments include:\n"{comments}"'

    @staticmethod
    def _translate_deal_blocks(deal_blocks: List[DealBlock]):
        deals = []
        counter = 1
        for deal_block in deal_blocks:
            deals.append((
                f'{counter}. {deal_block.owner.value} owns the deal named {deal_block.name.value}. '
                f'Contact involved in the deal is named {deal_block.contact.value}. '
                f'Deal is of type {deal_block.type} and is in stage {deal_block.stage}. '
                f'Deal is expected to close on {deal_block.close_date} and is worth {deal_block.amount} '
                f'with a {deal_block.probability}% probability of closing.'
            ))
            counter += 1
        deals = '\n'.join(deals)
        return f'Page\'s deals include:\n"{deals}"'

    @staticmethod
    def _translate_contact_blocks(contact_blocks: List[ContactBlock]):
        contacts = []
        counter = 1
        for contact_block in contact_blocks:
            contacts.append((
                f'{counter}. {contact_block.name.value} is a {contact_block.title} who works in the department {contact_block.department}. '
                f'Contact was created by {contact_block.created_by.value} and is a {contact_block.lead_source} lead.'
            ))
            counter += 1
        contacts = '\n'.join(contacts)
        return f'Page\'s contacts include:\n"{contacts}"'


def _get_sorted_blocks(block_streams: List[BlockStream]):
    blocks = {
        'body': [],
        'comment': [],
        'contact': [],
        'deal': [],
        'member': [],
        'summary': [],
        'title': []
    }
    for block_stream in block_streams:
        if block_stream.label == BodyBlock._LABEL:
            blocks['body'].extend(block_stream.blocks)
        elif block_stream.label == CommentBlock._LABEL:
            blocks['comment'].extend(block_stream.blocks)
        elif block_stream.label == ContactBlock._LABEL:
            blocks['contact'].extend(block_stream.blocks)
        elif block_stream.label == DealBlock._LABEL:
            blocks['deal'].extend(block_stream.blocks)
        elif block_stream.label == MemberBlock._LABEL:
            blocks['member'].extend(block_stream.blocks)
        elif block_stream.label == SummaryBlock._LABEL:
            blocks['summary'].extend(block_stream.blocks)
        elif block_stream.label == TitleBlock._LABEL:
            blocks['title'].extend(block_stream.blocks)
    return blocks

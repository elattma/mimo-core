from typing import List

from .blocks import (BlockStream, BodyBlock, CommentBlock, ContactBlock,
                     DealBlock, MemberBlock, Relations, SummaryBlock, TitleBlock)

SUPPORTED_BLOCK_LABELS = set([
    SummaryBlock._LABEL,
    BodyBlock._LABEL,
    MemberBlock._LABEL,
    TitleBlock._LABEL,
    CommentBlock._LABEL,
    DealBlock._LABEL,
    ContactBlock._LABEL
])

TRANSLATION_STARTS = {
    'google_mail': 'START OF EMAIL (Gmail)\n',
    'google_docs': 'START OF DOCUMENT (Google Docs)\n',
    'zoho': 'START OF CRM ACCOUNT (Zoho)\n',
    'zendesk': 'START OF CUSTOMER SUPPORT TICKET (Zendesk)\n'
}

TRANSLATION_ENDS = {
    'google_mail': 'END OF EMAIL\n',
    'google_docs': 'END OF DOCUMENT\n',
    'zoho': 'END OF CRM ACCOUNT\n',
    'zendesk': 'END OF CUSTOMER SUPPORT TICKET\n'
}


class Translator:
    def __init__(self) -> None:
        pass

    @staticmethod
    def translate_document(
        integration: str,
        block_streams: List[BlockStream]
    ) -> str:
        if not (integration and block_streams):
            return None
        translation = Translator._get_translation_start(integration)
        blocks = Translator._get_sorted_blocks(block_streams)

        if 'title' in blocks and blocks['title']:
            translation += Translator._translate_title_blocks(blocks['title'])
            translation += '\n'
        if 'member' in blocks and blocks['member']:
            translation += Translator._get_translation_end(integration)
            translation += '\n'
        if 'summary' in blocks and blocks['summary']:
            translation += Translator._translate_summary_blocks(
                blocks['summary']
            )
            translation += '\n'
        if 'body' in blocks and blocks['body']:
            translation += Translator._translate_body_blocks(blocks['body'])
            translation += '\n'
        if 'comment' in blocks and blocks['comment']:
            translation += Translator._translate_comment_blocks(
                blocks['comment']
            )
            translation += '\n'
        if 'deal' in blocks and blocks['deal']:
            translation += Translator._translate_deal_blocks(blocks['deal'])
            translation += '\n'
        if 'contact' in blocks and blocks['contact']:
            translation += Translator._translate_contact_blocks(
                blocks['contact']
            )
            translation += '\n'
        translation += Translator._get_translation_end(integration)
        return translation

    @staticmethod
    def _get_translation_start(integration: str) -> str:
        return TRANSLATION_STARTS[integration]

    @staticmethod
    def _get_translation_end(integration: str) -> str:
        return TRANSLATION_ENDS[integration]

    @staticmethod
    def translate_block_streams(block_streams: List[BlockStream]) -> str:
        if not block_streams:
            return None

        translated = []
        for block_stream in block_streams:
            if not (block_stream and block_stream.blocks
                    and block_stream.label
                    and block_stream.label in SUPPORTED_BLOCK_LABELS):
                print('[Translator] Invalid block stream!')
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
        for summary_block in summary_blocks:
            summaries.append(f'{summary_block.text}')
        summary = '\n'.join(summaries)
        return f'Summary:\n{summary}'

    @staticmethod
    def _translate_body_blocks(body_blocks: List[BodyBlock]):
        bodies = []
        for body_block in body_blocks:
            bodies.append(f'{body_block.text}')
        body = '\n'.join(bodies)
        return f'Body:\n{body}'

    @staticmethod
    def _translate_member_blocks(member_blocks: List[MemberBlock]):
        members = []
        for member_block in member_blocks:
            members.append((
                f'\t{member_block.name.value}:\n'
                f'\t\tEmail: {member_block.name.id}\n'
                f'\t\tRole: {member_block.relation.value}'
            ))
        members = '\n'.join(members)
        return f'Members:\n{members}'

    @staticmethod
    def _translate_title_blocks(title_blocks: List[TitleBlock]):
        titles = []
        for title_block in title_blocks:
            titles.append(f'{title_block.text}')
        titles = '\n'.join(titles)
        return f'Title(s):\n{titles}'

    @staticmethod
    def _translate_comment_blocks(comment_blocks: List[CommentBlock]):
        comments = []
        for comment_block in comment_blocks:
            comments.append(
                f'{comment_block.author} said:\n"{comment_block.text}"')
        comments = '\n'.join(comments)
        return f'Comments:\n{comments}'

    @staticmethod
    def _translate_deal_blocks(deal_blocks: List[DealBlock]):
        deals = []
        for deal_block in deal_blocks:
            deals.append((
                f'\t{deal_block.name.value}:\n'
                f'\t\tOwner: {deal_block.owner.value}\n'
                f'\t\tPrimary contact: {deal_block.contact.value}\n'
                f'\t\tType: {deal_block.type}\n'
                f'\t\tStage: {deal_block.stage}\n'
                f'\t\tClose date: {deal_block.close_date}\n'
                f'\t\tAmount: {deal_block.amount}\n'
                f'\t\tProbability of closing: {deal_block.probability}%'
            ))
        deals = '\n'.join(deals)
        return f'Deals:\n{deals}'

    @staticmethod
    def _translate_contact_blocks(contact_blocks: List[ContactBlock]):
        contacts = []
        for contact_block in contact_blocks:
            contacts.append((
                f'\t{contact_block.name.value}:\n'
                f'\t\tEmail: {contact_block.name.id}\n'
                f'\t\tTitle: {contact_block.title}\n'
                f'\t\tDepartment: {contact_block.department}\n'
                f'\t\tCreated by: {contact_block.created_by.value}\n'
                f'\t\tLead source: {contact_block.lead_source}\n'
            ))
        contacts = '\n'.join(contacts)
        return f'Contacts:\n{contacts}'

    @staticmethod
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
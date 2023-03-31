from dataclasses import dataclass
from typing import Dict, List
from app.mrkl.prompt import ChatPrompt, ChatPromptMessage, ChatPromptMessageRole

from app.mystery.data_agent import (BlockDescription, ContextBasket,
                                    DataAgent, Source)

SYSTEM_MESSAGE_CONTENT = '''Pretend you are AnswerGPT. Your job is to answer a question using the context you are given.
The available context can be found below.
--------
{context}
'''

@dataclass
class Answer:
    content: str
    sources: List[Source]

class QuestionAnswerAgent(DataAgent):
    # TODO: Move data_sources and block_descriptions to the constructor
    def run(
        self,
        question: str,
        data_sources: List[str],
    ) -> Answer:
        query = self.create_query(
            question,
            data_sources,
        )
        context_basket = self.execute_query(query)
        answer = self._use_context_to_answer_question(question, context_basket)
        return answer

    def debug_run(
        self,
        question: str,
        data_sources: List[str],
    ) -> Answer:
        print('[QuestionAnswerAgent] Running debug_run...\n')
        print('[QuestionAnswerAgent] Received question...')
        print(question, '\n')
        print('[QuestionAnswerAgent] Creating query...')
        query = self.create_query(
            question,
            data_sources,
        )
        print(query, '\n')
        print('[QuestionAnswerAgent] Executing query...')
        context_basket = self.execute_query(query)
        print(context_basket, '\n')
        print('[QuestionAnswerAgent] Using context to answer question...')
        answer = self._use_context_to_answer_question(question, context_basket)
        print(answer, '\n')
        return answer

    def _use_context_to_answer_question(
        self,
        question: str,
        context_basket: ContextBasket
    ) -> Answer:
        context = '\n\n'.join([context.content for context in context_basket])
        system_message = ChatPromptMessage(
            role=ChatPromptMessageRole.SYSTEM.value,
            content=SYSTEM_MESSAGE_CONTENT.format(context=context)
        )
        user_message = ChatPromptMessage(
            role=ChatPromptMessageRole.USER.value,
            content=question
        )
        prompt = ChatPrompt(messages=[system_message, user_message])
        llm_output = self._llm.predict(prompt)
        sources = [context.source for context in context_basket]
        return Answer(content=llm_output, sources=sources)



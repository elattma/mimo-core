from dataclasses import dataclass
from typing import List

from .data_agent import ContextBasket, DataAgent, Source
from .mrkl.prompt import ChatPrompt, ChatPromptMessage, ChatPromptMessageRole

SYSTEM_MESSAGE_CONTENT = '''Pretend you are AnswerGPT. Your job is to answer a question using the context you are given.
The available context can be found below.
--------
{context}
'''

MAX_TOKENS = 2048

@dataclass
class Answer:
    content: str
    sources: List[Source]

class QuestionAnswerAgent(DataAgent):
    def run(
        self,
        question: str,
    ) -> Answer:
        context_basket = self.generate_context(question)
        if self._context_basket_token_size(context_basket) > MAX_TOKENS:
            return 'I received context that was too long to respond to.'
        answer = self._use_context_to_answer_question(question, context_basket)
        return answer

    def debug_run(
        self,
        question: str
    ) -> Answer:
        print('[QuestionAnswerAgent] Generating context...')
        context_basket = self.generate_context(question)
        print('[QuestionAnswerAgent] Context generated...')
        print(context_basket, '\n')
        if self._context_basket_token_size(context_basket) > MAX_TOKENS:
            return 'I received context that was too long to respond to.'
        print('[QuestionAnswerAgent] Using context to answer question...')
        answer = self._use_context_to_answer_question(question, context_basket)
        print('[QuestionAnswerAgent] Answer received...')
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

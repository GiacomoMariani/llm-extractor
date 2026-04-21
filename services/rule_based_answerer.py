import re

from models.answering import AnswerResponse


class RuleBasedAnswerer:
    async def answer(self, question: str, context: str) -> AnswerResponse:
        normalized_question = question.strip().lower()
        normalized_context = context.strip()

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", normalized_context)
            if sentence.strip()
        ]

        question_words = {
            word
            for word in re.findall(r"\b\w+\b", normalized_question)
            if len(word) > 2
        }

        best_sentence = None
        best_score = -1

        for sentence in sentences:
            sentence_words = {
                word
                for word in re.findall(r"\b\w+\b", sentence.lower())
                if len(word) > 2
            }

            score = len(question_words.intersection(sentence_words))

            if score > best_score:
                best_score = score
                best_sentence = sentence

        if best_sentence:
            return AnswerResponse(answer=best_sentence)

        return AnswerResponse(answer="I could not find the answer in the provided context.")
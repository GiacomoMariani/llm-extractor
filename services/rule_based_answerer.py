import re

from models.answering import AnswerResponse

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by",
    "did", "do", "does", "for", "from", "has", "have",
    "how", "in", "is", "it", "of", "on", "or", "that",
    "the", "this", "to", "was", "what", "when", "where",
    "which", "who", "why", "with",
}

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
            if len(word) > 2 and word not in STOPWORDS
        }

        best_sentence = None
        best_score = 0

        for sentence in sentences:
            candidate_words = {
                word
                for word in re.findall(r"\b\w+\b", sentence.lower())
                if len(word) > 2 and word not in STOPWORDS
            }

            score = len(question_words.intersection(candidate_words))

            if score > best_score:
                best_score = score
                best_sentence = sentence

        if best_sentence:
            return AnswerResponse(
                answer=best_sentence,
                was_fallback=False,
            )

        return AnswerResponse(
            answer="I could not find the answer in the provided context.",
            was_fallback=True,
        )
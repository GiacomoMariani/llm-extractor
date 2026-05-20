import re
from typing import Any

from models.answering import AnswerResponse

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "did",
    "do",
    "does",
    "for",
    "from",
    "has",
    "have",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}

QUICK_REFERENCE_FIELDS: list[dict[str, Any]] = [
    {
        "label": "Standard support hours",
        "required_terms": {"standard", "support", "hours"},
        "template": "Standard support hours are {value}.",
    },
    {
        "label": "First response target",
        "required_terms": {"first", "response", "target"},
        "template": "The first response target is {value}.",
    },
    {
        "label": "Delivery window",
        "required_terms": {"delivery"},
        "template": "Standard demo order delivery takes {value}.",
    },
    {
        "label": "Refund review window",
        "required_terms": {"refund", "review"},
        "template": "Refund review takes {value}.",
    },
    {
        "label": "Escalation trigger",
        "required_terms": {"escalation"},
        "template": "The escalation trigger is {value}.",
    },
]


class RuleBasedAnswerer:
    async def answer(self, question: str, context: str) -> AnswerResponse:
        normalized_question = question.strip().lower()
        normalized_context = context.strip()

        question_words = self._content_words(normalized_question)

        quick_reference_answer = self._answer_from_quick_reference(
            question_words=question_words,
            context=normalized_context,
        )

        if quick_reference_answer:
            return AnswerResponse(
                answer=quick_reference_answer,
                was_fallback=False,
            )

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", normalized_context)
            if sentence.strip()
        ]

        best_sentence = None
        best_score = 0

        for sentence in sentences:
            candidate_words = self._content_words(sentence.lower())
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

    def _answer_from_quick_reference(
        self,
        question_words: set[str],
        context: str,
    ) -> str | None:
        normalized_context = " ".join(context.split())
        boundary_labels = "|".join(
            re.escape(field["label"])
            for field in QUICK_REFERENCE_FIELDS
        )

        for field in QUICK_REFERENCE_FIELDS:
            required_terms = field["required_terms"]

            if not required_terms.issubset(question_words):
                continue

            match = re.search(
                rf"{re.escape(field['label'])}\s+(.+?)(?=\s+(?:{boundary_labels})\s+|$)",
                normalized_context,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            value = self._clean_extracted_value(match.group(1))

            if not value:
                continue

            return field["template"].format(value=value)

        return None

    def _clean_extracted_value(self, value: str) -> str:
        cleaned = " ".join(value.split())
        cleaned = cleaned.rstrip(" .")

        return cleaned

    def _content_words(self, text: str) -> set[str]:
        return {
            word
            for word in re.findall(r"\b\w+\b", text)
            if len(word) > 2 and word not in STOPWORDS
        }

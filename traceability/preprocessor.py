import re
from typing import List, Set

CODE_STOPWORDS: Set[str] = {
    # Python keywords
    "def", "class", "self", "return", "import", "from", "as", "if", "elif", "else",
    "for", "while", "break", "continue", "pass", "try", "except", "finally", "raise",
    "with", "yield", "lambda", "async", "await", "none", "true", "false", "in", "is",
    "not", "and", "or", "global", "nonlocal", "assert",
    # Common code terms & generic tokens
    "args", "kwargs", "str", "int", "float", "bool", "list", "dict", "set", "tuple",
    "optional", "any", "union", "init", "none", "object", "type", "val", "var",
    # English stopwords
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with",
    "by", "about", "against", "between", "into", "through", "during", "before",
    "after", "above", "below", "from", "up", "down", "of", "off", "over", "under",
    "again", "further", "then", "once", "here", "there", "when", "where", "why",
    "how", "all", "any", "both", "each", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "s", "t", "can", "will", "just", "don", "should", "now", "this", "that", "these",
    "those", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "having", "do", "does", "did", "doing", "must", "shall", "it", "its"
}


class CodePreprocessor:
    """
    Code-aware preprocessor for Software Engineering artifacts.
    Handles identifier splitting (camelCase, snake_case), programming stopword removal,
    and term normalization.
    """

    @staticmethod
    def split_identifiers(text: str) -> str:
        """
        Splits camelCase and PascalCase into separate words:
        e.g., 'processPayment' -> 'process Payment'
              'HTTPRequest' -> 'HTTP Request'
        """
        # Split camelCase and PascalCase
        s1 = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', text)
        s2 = re.sub(r'([A-Z]+)([A-Z][a-z0-9])', r'\1 \2', s1)
        # Split snake_case and kebab-case
        s3 = re.sub(r'[_.\-:/\\()[\],]', ' ', s2)
        return s3

    @staticmethod
    def stem_suffix(word: str) -> str:
        """Lightweight algorithmic stemmer for common inflectional suffixes."""
        if len(word) <= 3:
            return word
        if word.endswith("ing") and len(word) > 5:
            return word[:-3]
        if word.endswith("tion") and len(word) > 5:
            return word[:-4] + "t"
        if word.endswith("ed") and len(word) > 4:
            return word[:-2]
        if word.endswith("es") and len(word) > 4:
            return word[:-2]
        if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
            return word[:-1]
        if word.endswith("ment") and len(word) > 6:
            return word[:-4]
        return word

    @classmethod
    def preprocess(cls, text: str, stem: bool = True) -> List[str]:
        """
        Full text preprocessing pipeline:
        1. Split compound identifiers
        2. Lowercase and tokenize alphanumeric terms
        3. Remove code and natural language stopwords
        4. Normalize/stem terms
        """
        if not text:
            return []

        expanded = cls.split_identifiers(text)
        tokens = re.findall(r'[a-zA-Z0-9]+', expanded.lower())

        clean_tokens = []
        for token in tokens:
            if len(token) < 2 or token.isdigit():
                continue
            if token in CODE_STOPWORDS:
                continue
            if stem:
                token = cls.stem_suffix(token)
            clean_tokens.append(token)

        return clean_tokens

    @classmethod
    def preprocess_to_string(cls, text: str) -> str:
        return " ".join(cls.preprocess(text))

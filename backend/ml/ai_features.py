import re
import math
from typing import Dict, Any, List


TEXTBOOK_IDENTIFIERS = {
    "result", "res", "data", "item", "temp", "response", "payload", 
    "helper", "output", "val", "value", "element", "params", "current",
    "obj", "entry", "record", "target", "source", "config", "items"
}

TEMPLATED_DOCSTRING_PATTERNS = [
    r"args\s*:",
    r"returns\s*:",
    r"raises\s*:",
    r":param\s+\w+:",
    r":return:",
    r"initialize\s+the\s+",
    r"helper\s+(function|method)\s+to\s+",
    r"represents\s+a\s+",
    r"calculate\s+the\s+",
    r"determines\s+whether\s+",
    r"creates\s+a\s+new\s+",
]

TRIVIAL_COMMENT_PATTERNS = [
    r"#\s*return\s+(the\s+)?(result|value|data|response)",
    r"#\s*initialize\s+(the\s+)?",
    r"#\s*loop\s+(through|over)\s+",
    r"#\s*check\s+if\s+",
    r"#\s*increment\s+",
    r"#\s*set\s+default\s+",
    r"#\s*handle\s+error",
    r"#\s*close\s+(connection|file)",
    r"#\s*parse\s+",
    r"#\s*print\s+",
    r"//\s*return\s+(the\s+)?(result|value|data|response)",
    r"//\s*initialize\s+",
    r"//\s*loop\s+(through|over)\s+",
    r"//\s*check\s+if\s+",
]

SCAFFOLDING_PATTERNS = [
    r"#\s*example\s+usage\s*:",
    r"//\s*example\s+usage\s*:",
    r"#\s*example\s*:",
    r"#\s*output\s*:",
    r"#\s*step\s+\d+\s*:",
    r"#\s*\d+\.\s+[A-Z]",
    r"if\s+__name__\s*==\s*['\"]__main__['\"]\s*:",
]


def shannon_entropy(text: str) -> float:
    """Calculates character-level Shannon entropy of a string."""
    if not text:
        return 0.0
    text_lower = text.lower()
    counts = {}
    for c in text_lower:
        counts[c] = counts.get(c, 0) + 1
    total = len(text_lower)
    ent = 0.0
    for c, cnt in counts.items():
        p = cnt / total
        ent -= p * math.log2(p)
    return round(ent, 4)


class AIFeatureExtractor:
    FEATURE_NAMES = [
        "casing_consistency",
        "indent_regularity",
        "line_length_std",
        "comment_density",
        "templated_docstring_density",
        "trivial_comment_density",
        "identifier_entropy",
        "textbook_var_ratio",
        "defensive_error_density",
        "type_annotation_density",
        "scaffolding_score",
        "docstring_presence_ratio",
    ]

    @classmethod
    def extract_features(cls, content: str, language: str = "python") -> Dict[str, float]:
        """Extract a structured numeric vector of AI code markers from source code text."""
        lines = content.splitlines()
        total_lines = len(lines)
        non_empty_lines = [line for line in lines if line.strip()]
        non_empty_count = max(len(non_empty_lines), 1)

        # 1. Stylistic Regularity
        # A. Indentation regularity
        indents = []
        for line in non_empty_lines:
            match = re.match(r"^(\s*)", line)
            if match:
                indents.append(len(match.group(1)))
        if len(indents) > 1:
            diffs = [abs(indents[i] - indents[i - 1]) for i in range(1, len(indents))]
            mean_diff = sum(diffs) / len(diffs)
            var_diff = sum((d - mean_diff) ** 2 for d in diffs) / len(diffs)
            indent_regularity = max(0.0, 1.0 - min(1.0, math.sqrt(var_diff) / 8.0))
        else:
            indent_regularity = 0.5

        # B. Line length standard deviation
        line_lens = [len(line) for line in non_empty_lines]
        if line_lens:
            mean_len = sum(line_lens) / len(line_lens)
            var_len = sum((l - mean_len) ** 2 for l in line_lens) / len(line_lens)
            line_length_std = round(math.sqrt(var_len), 2)
        else:
            line_length_std = 25.0

        # C. Identifier Casing Consistency
        identifiers = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", content)
        keywords = {
            "def", "class", "return", "import", "from", "as", "if", "elif", "else", 
            "for", "while", "in", "is", "not", "and", "or", "try", "except", "finally", 
            "with", "raise", "pass", "break", "continue", "lambda", "yield", "async", 
            "await", "function", "const", "let", "var", "true", "false", "null", "none"
        }
        user_ids = [ident for ident in identifiers if ident.lower() not in keywords and len(ident) > 1]
        
        snake_count = 0
        camel_count = 0
        pascal_count = 0
        for ident in user_ids:
            if "_" in ident and ident.islower():
                snake_count += 1
            elif ident[0].isupper() and any(c.islower() for c in ident[1:]):
                pascal_count += 1
            elif ident[0].islower() and any(c.isupper() for c in ident[1:]):
                camel_count += 1

        total_classified = snake_count + camel_count + pascal_count
        if total_classified > 3:
            max_case = max(snake_count, camel_count, pascal_count)
            casing_consistency = round(max_case / total_classified, 3)
        else:
            casing_consistency = 0.7

        # 2. Comment & Docstring Patterns
        comment_lines = 0
        trivial_comment_count = 0
        templated_docstring_matches = 0
        scaffolding_matches = 0

        for line in lines:
            line_str = line.strip()
            if line_str.startswith("#") or line_str.startswith("//") or line_str.startswith("/*") or line_str.startswith("*"):
                comment_lines += 1
            for p in TRIVIAL_COMMENT_PATTERNS:
                if re.search(p, line_str, re.IGNORECASE):
                    trivial_comment_count += 1
            for p in SCAFFOLDING_PATTERNS:
                if re.search(p, line_str, re.IGNORECASE):
                    scaffolding_matches += 1

        content_lower = content.lower()
        for p in TEMPLATED_DOCSTRING_PATTERNS:
            templated_docstring_matches += len(re.findall(p, content_lower))

        comment_density = round(comment_lines / non_empty_count, 3)
        templated_docstring_density = round(templated_docstring_matches / max(non_empty_count / 25.0, 1.0), 3)
        trivial_comment_density = round(trivial_comment_count / max(non_empty_count / 30.0, 1.0), 3)
        scaffolding_score = round(min(1.0, scaffolding_matches / 2.0), 2)

        func_class_count = len(re.findall(r"\b(def|class|function)\s+\w+", content))
        triple_quotes = len(re.findall(r"(\"\"\"|'''|\/\*\*)", content)) // 2
        docstring_presence_ratio = round(min(1.0, triple_quotes / max(func_class_count, 1)), 2)

        # 3. Structural Signals
        if user_ids:
            all_ids_text = "".join(user_ids)
            identifier_entropy = shannon_entropy(all_ids_text)
        else:
            identifier_entropy = 3.8

        textbook_hits = sum(1 for ident in user_ids if ident.lower() in TEXTBOOK_IDENTIFIERS)
        textbook_var_ratio = round(textbook_hits / max(len(user_ids), 1), 3)

        try_matches = len(re.findall(r"\b(try|catch|except)\b", content))
        defensive_error_density = round(try_matches / max(non_empty_count / 40.0, 1.0), 3)

        type_hints = len(re.findall(r"(->\s*\w+|:\s*(int|str|float|bool|list|dict|any|tuple|optional|number|string|void)\b)", content, re.IGNORECASE))
        type_annotation_density = round(type_hints / max(non_empty_count / 20.0, 1.0), 3)

        features = {
            "casing_consistency": casing_consistency,
            "indent_regularity": indent_regularity,
            "line_length_std": line_length_std,
            "comment_density": comment_density,
            "templated_docstring_density": templated_docstring_density,
            "trivial_comment_density": trivial_comment_density,
            "identifier_entropy": identifier_entropy,
            "textbook_var_ratio": textbook_var_ratio,
            "defensive_error_density": defensive_error_density,
            "type_annotation_density": type_annotation_density,
            "scaffolding_score": scaffolding_score,
            "docstring_presence_ratio": docstring_presence_ratio,
        }

        return features

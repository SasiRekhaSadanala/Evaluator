"""
Unified AST-based code parser using tree-sitter.

Replaces the fragmented ast.parse() + regex approach with a single
parser that works for Python, C++, Java, and JavaScript — producing
identical feature dictionaries regardless of language.

v2.1 — Added advanced complexity metrics:
  - function_names, identifier_count, max_nesting_depth
  - unique_identifiers, complexity_score
"""

import re
from typing import Dict, List, Optional, Set

# Lazy-load tree-sitter to avoid import errors if not installed
_TREE_SITTER_AVAILABLE = False
_LANGUAGES = {}

def _init_tree_sitter():
    """One-time initialization of tree-sitter languages."""
    global _TREE_SITTER_AVAILABLE, _LANGUAGES
    if _LANGUAGES:
        return  # Already initialized

    try:
        from tree_sitter import Language, Parser

        try:
            import tree_sitter_python as tspython
            _LANGUAGES["python"] = Language(tspython.language())
        except Exception:
            pass

        try:
            import tree_sitter_cpp as tscpp
            _LANGUAGES["cpp"] = Language(tscpp.language())
        except Exception:
            pass

        if _LANGUAGES:
            _TREE_SITTER_AVAILABLE = True
        else:
            print("WARNING: tree-sitter grammars not found. Falling back to regex mode.")
    except ImportError:
        print("WARNING: tree-sitter not installed. Falling back to regex mode.")


# ---------------------------------------------------------------------------
# Node-type → feature mapping per language
# ---------------------------------------------------------------------------

NODE_TYPE_MAP = {
    "python": {
        "function_definition": "functions",
        "class_definition": "classes",
        "for_statement": "loops",
        "while_statement": "loops",
        "if_statement": "conditions",
        "try_statement": "error_handling",
        "except_clause": "error_handling",
    },
    "cpp": {
        "function_definition": "functions",
        "function_declarator": "functions",
        "class_specifier": "classes",
        "struct_specifier": "classes",
        "for_statement": "loops",
        "for_range_loop": "loops",
        "while_statement": "loops",
        "do_statement": "loops",
        "if_statement": "conditions",
        "switch_statement": "conditions",
        "try_statement": "error_handling",
        "catch_clause": "error_handling",
    },
}

# Node types that contribute to nesting depth
NESTING_NODES = {
    "python": {"for_statement", "while_statement", "if_statement", "try_statement",
               "function_definition", "class_definition", "with_statement"},
    "cpp": {"for_statement", "for_range_loop", "while_statement", "do_statement",
            "if_statement", "switch_statement", "try_statement",
            "function_definition", "class_specifier"},
}

# Node types that represent identifiers
IDENTIFIER_NODES = {
    "python": {"identifier"},
    "cpp": {"identifier", "field_identifier", "type_identifier"},
}

# Node types that represent function/method names
FUNCTION_NAME_NODES = {
    "python": {"function_definition"},
    "cpp": {"function_definition", "function_declarator"},
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def is_available() -> bool:
    """Check if tree-sitter is available."""
    _init_tree_sitter()
    return _TREE_SITTER_AVAILABLE


def supports_language(lang: str) -> bool:
    """Check if a specific language grammar is loaded."""
    _init_tree_sitter()
    return lang in _LANGUAGES


def extract_features(code: str, lang: str) -> Dict:
    """
    Parse code and extract structural features + complexity metrics.

    Args:
        code: Source code string.
        lang: Language key ("python", "cpp").

    Returns:
        Dictionary with counts and complexity metrics::

            {
                "functions": int,
                "classes": int,
                "loops": int,
                "conditions": int,
                "error_handling": int,
                "has_syntax_error": bool,
                "total_nodes": int,
                "parser_mode": "tree-sitter" | "regex",
                # --- New v2.1 fields ---
                "function_names": List[str],
                "identifier_count": int,
                "unique_identifiers": int,
                "max_nesting_depth": int,
                "complexity_score": float,  # 0-100 composite
            }
    """
    _init_tree_sitter()

    if _TREE_SITTER_AVAILABLE and lang in _LANGUAGES:
        return _extract_with_tree_sitter(code, lang)
    else:
        return _extract_with_regex(code, lang)


# ---------------------------------------------------------------------------
# tree-sitter implementation
# ---------------------------------------------------------------------------

def _extract_with_tree_sitter(code: str, lang: str) -> Dict:
    """Extract features using tree-sitter AST walk."""
    from tree_sitter import Parser

    parser = Parser(_LANGUAGES[lang])
    tree = parser.parse(code.encode("utf-8"))

    counts = {
        "functions": 0,
        "classes": 0,
        "loops": 0,
        "conditions": 0,
        "error_handling": 0,
    }

    type_map = NODE_TYPE_MAP.get(lang, {})
    nesting_types = NESTING_NODES.get(lang, set())
    id_types = IDENTIFIER_NODES.get(lang, {"identifier"})

    total_nodes = 0
    function_names: List[str] = []
    identifiers: Set[str] = set()
    identifier_count = 0
    max_depth = 0

    def walk(node, depth=0):
        nonlocal total_nodes, max_depth, identifier_count
        total_nodes += 1

        # Track nesting depth
        if node.type in nesting_types:
            depth += 1
            if depth > max_depth:
                max_depth = depth

        # Count structural features
        if node.type in type_map:
            feature_key = type_map[node.type]
            counts[feature_key] += 1

        # Extract function/method names
        if node.type == "function_definition":
            # The function name is the first 'identifier' child
            for child in node.children:
                if child.type == "identifier":
                    function_names.append(child.text.decode("utf-8"))
                    break
        elif node.type == "function_declarator":
            # C++ function_declarator has an identifier child
            for child in node.children:
                if child.type in ("identifier", "field_identifier"):
                    function_names.append(child.text.decode("utf-8"))
                    break

        # Collect identifiers
        if node.type in id_types:
            name = node.text.decode("utf-8")
            identifiers.add(name)
            identifier_count += 1

        for child in node.children:
            walk(child, depth)

    walk(tree.root_node)

    # Compute composite complexity score (0-100)
    complexity = _compute_complexity(
        functions=counts["functions"],
        classes=counts["classes"],
        loops=counts["loops"],
        conditions=counts["conditions"],
        error_handling=counts["error_handling"],
        max_depth=max_depth,
        unique_ids=len(identifiers),
        total_nodes=total_nodes,
        code=code,
    )

    counts["has_syntax_error"] = tree.root_node.has_error
    counts["total_nodes"] = total_nodes
    counts["parser_mode"] = "tree-sitter"
    counts["function_names"] = function_names
    counts["identifier_count"] = identifier_count
    counts["unique_identifiers"] = len(identifiers)
    counts["max_nesting_depth"] = max_depth
    counts["complexity_score"] = complexity
    return counts


# ---------------------------------------------------------------------------
# Regex fallback (same logic as old code_agent, but returns the same dict)
# ---------------------------------------------------------------------------

def _extract_with_regex(code: str, lang: str) -> Dict:
    """
    Fallback: extract features using regex and Python's ast module.

    Returns the same dict shape as tree-sitter, so callers don't care
    which mode was used.
    """
    counts = {
        "functions": 0,
        "classes": 0,
        "loops": 0,
        "conditions": 0,
        "error_handling": 0,
        "has_syntax_error": False,
        "total_nodes": 0,
        "parser_mode": "regex",
    }

    function_names: List[str] = []
    identifiers: Set[str] = set()
    max_depth = 0

    if lang == "python":
        try:
            import ast
            tree = ast.parse(code)

            def _walk_depth(node, depth=0):
                nonlocal max_depth
                counts["total_nodes"] += 1

                if isinstance(node, ast.FunctionDef):
                    counts["functions"] += 1
                    function_names.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    counts["classes"] += 1
                elif isinstance(node, (ast.For, ast.While)):
                    counts["loops"] += 1
                    depth += 1
                elif isinstance(node, ast.If):
                    counts["conditions"] += 1
                    depth += 1
                elif isinstance(node, (ast.Try, ast.ExceptHandler)):
                    counts["error_handling"] += 1
                elif isinstance(node, ast.Name):
                    identifiers.add(node.id)

                if depth > max_depth:
                    max_depth = depth

                for child in ast.iter_child_nodes(node):
                    _walk_depth(child, depth)

            _walk_depth(tree)
        except SyntaxError:
            counts["has_syntax_error"] = True

    elif lang == "cpp":
        # Regex patterns for C++ structural elements
        counts["functions"] = len(re.findall(
            r'(?:[\w:]+\s+)+(\w+)\s*\([^)]*\)\s*(?:const\s*)?(?:override\s*)?(?:noexcept\s*)?\{', code
        ))
        counts["classes"] = len(re.findall(r'\bclass\s+\w+', code))
        counts["loops"] = (
            len(re.findall(r'\bfor\s*\(', code))
            + len(re.findall(r'\bwhile\s*\(', code))
            + len(re.findall(r'\bdo\s*\{', code))
        )
        counts["conditions"] = (
            len(re.findall(r'\bif\s*\(', code))
            + len(re.findall(r'\bswitch\s*\(', code))
        )
        counts["error_handling"] = (
            len(re.findall(r'\btry\s*\{', code))
            + len(re.findall(r'\bcatch\s*\(', code))
        )
        counts["total_nodes"] = sum(v for k, v in counts.items() if isinstance(v, int))

        # Extract function names via regex
        fn_matches = re.findall(r'(?:[\w:]+\s+)+(\w+)\s*\(', code)
        function_names = [m for m in fn_matches if m not in ('if', 'for', 'while', 'switch', 'catch')]

        # Extract identifiers via regex
        all_ids = set(re.findall(r'\b([a-zA-Z_]\w*)\b', code))
        cpp_keywords = {'int', 'float', 'double', 'char', 'void', 'bool', 'string',
                        'return', 'if', 'else', 'for', 'while', 'do', 'switch', 'case',
                        'break', 'continue', 'class', 'struct', 'public', 'private',
                        'protected', 'virtual', 'override', 'const', 'static', 'namespace',
                        'using', 'include', 'define', 'ifndef', 'endif', 'std', 'cout',
                        'cin', 'endl', 'vector', 'map', 'set', 'main', 'true', 'false',
                        'nullptr', 'new', 'delete', 'try', 'catch', 'throw'}
        identifiers = all_ids - cpp_keywords

        # Estimate nesting depth from indentation
        lines = code.split('\n')
        for line in lines:
            stripped = line.lstrip()
            if stripped:
                indent = len(line) - len(stripped)
                # Rough: each 4 spaces ≈ 1 level of nesting
                depth = indent // 4
                if depth > max_depth:
                    max_depth = depth

    # Compute complexity
    complexity = _compute_complexity(
        functions=counts["functions"],
        classes=counts["classes"],
        loops=counts["loops"],
        conditions=counts["conditions"],
        error_handling=counts["error_handling"],
        max_depth=max_depth,
        unique_ids=len(identifiers),
        total_nodes=counts["total_nodes"],
        code=code,
    )

    counts["function_names"] = function_names
    counts["identifier_count"] = len(identifiers)
    counts["unique_identifiers"] = len(identifiers)
    counts["max_nesting_depth"] = max_depth
    counts["complexity_score"] = complexity
    return counts


# ---------------------------------------------------------------------------
# Complexity scoring (shared by both modes)
# ---------------------------------------------------------------------------

def _compute_complexity(
    functions: int,
    classes: int,
    loops: int,
    conditions: int,
    error_handling: int,
    max_depth: int,
    unique_ids: int,
    total_nodes: int,
    code: str,
) -> float:
    """
    Compute a composite complexity score (0-100) from parsed features.

    This score DIFFERENTIATES structurally similar submissions by weighting:
    - Cyclomatic complexity approximation (conditions + loops + 1)
    - Nesting depth (deeper = more complex logic)
    - Identifier diversity (more unique names = more specific logic)
    - Code volume (total AST nodes)
    - Edge-case handling (error handling, boundary checks)

    Returns:
        Float between 0 and 100.
    """
    # Cyclomatic complexity ≈ conditions + loops + 1
    cyclomatic = conditions + loops + 1

    # Weighted components (each normalized to ~0-25 range, total max ~100)
    score = 0.0

    # Component 1: Cyclomatic complexity (0-30 points)
    # Typical range: 1-15 for student code
    score += min(cyclomatic * 3.0, 30.0)

    # Component 2: Nesting depth (0-20 points)
    # Typical range: 1-6 for student code
    score += min(max_depth * 4.0, 20.0)

    # Component 3: Identifier diversity (0-20 points)
    # Typical range: 5-30 unique identifiers
    score += min(unique_ids * 1.0, 20.0)

    # Component 4: Structural richness — functions + classes (0-15 points)
    score += min((functions + classes) * 5.0, 15.0)

    # Component 5: Code volume — total lines (0-15 points)
    code_lines = len([l for l in code.split('\n') if l.strip()])
    score += min(code_lines * 0.5, 15.0)

    return round(min(score, 100.0), 1)

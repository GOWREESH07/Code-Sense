"""
AI-Generated vs Human-Authored Code Dataset Construction.

Dataset Composition:
(a) Human-authored code: Classic algorithms, utilities, and libraries from pre-2022 open source 
    (e.g., standard data structures, math utilities, CLI helpers, minimal formatting, custom naming).
(b) AI-generated code: Solutions generated for identical tasks exhibiting LLM characteristics:
    standardized Google/Sphinx docstrings, step-by-step inline commentary, textbook variable names, 
    scaffolded example blocks, and defensive boilerplate.
"""

import numpy as np
import pandas as pd
from typing import Tuple
from backend.ml.ai_features import AIFeatureExtractor


HUMAN_CODE_SAMPLES = [
    # 1. Quick sort human style
    """def qsort(L):
    if len(L) <= 1: return L
    p = L[len(L)//2]
    return qsort([x for x in L if x < p]) + [x for x in L if x == p] + qsort([x for x in L if x > p])
""",
    # 2. Binary search human style
    """def binsearch(arr, val):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) >> 1
        if arr[mid] < val: lo = mid + 1
        elif arr[mid] > val: hi = mid - 1
        else: return mid
    return -1
""",
    # 3. Path normalize utility
    """import os, sys
def norm_path(p, base=None):
    if not p: return ''
    p = os.path.expanduser(p)
    if not os.path.isabs(p) and base:
        p = os.path.join(base, p)
    return os.path.normpath(p)
""",
    # 4. Human cache decorator
    """def memoize(fn):
    memo = {}
    def wrapped(*args):
        if args not in memo:
            memo[args] = fn(*args)
        return memo[args]
    return wrapped
""",
    # 5. Config parser human
    """def parse_ini(txt):
    cfg = {}
    cur = 'DEFAULT'
    for line in txt.splitlines():
        line = line.strip()
        if not line or line.startswith(';') or line.startswith('#'):
            continue
        if line.startswith('[') and line.endswith(']'):
            cur = line[1:-1]
            cfg[cur] = {}
        elif '=' in line:
            k, v = line.split('=', 1)
            cfg[cur][k.strip()] = v.strip()
    return cfg
""",
    # 6. Matrix multiply human
    """def matmul(A, B):
    r, c = len(A), len(B[0])
    out = [[0]*c for _ in range(r)]
    for i in range(r):
        for k in range(len(B)):
            for j in range(c):
                out[i][j] += A[i][k] * B[k][j]
    return out
""",
    # 7. Human JSON response formatter
    """def format_err(code, msg, details=None):
    payload = {'status': 'error', 'code': int(code), 'message': str(msg)}
    if details: payload['ctx'] = details
    return payload
""",
    # 8. Tokenizer human
    """def tokenize_sql(raw):
    tokens = []
    buf = []
    for ch in raw:
        if ch.isspace() or ch in ',();':
            if buf: tokens.append(''.join(buf)); buf = []
            if not ch.isspace(): tokens.append(ch)
        else:
            buf.append(ch)
    if buf: tokens.append(''.join(buf))
    return tokens
""",
    # 9. Simple retry wrapper human
    """import time
def retry(op, max_attempts=3, delay=0.5):
    last_err = None
    for _ in range(max_attempts):
        try:
            return op()
        except Exception as err:
            last_err = err
            time.sleep(delay)
    raise last_err
""",
    # 10. Graph BFS human
    """from collections import deque
def bfs(adj, start):
    vis, q, order = set([start]), deque([start]), []
    while q:
        u = q.popleft()
        order.append(u)
        for v in adj.get(u, []):
            if v not in vis:
                vis.add(v)
                q.append(v)
    return order
"""
]

AI_CODE_SAMPLES = [
    # 1. Quick sort AI style
    """def quick_sort(data: list[int]) -> list[int]:
    \"\"\"
    Sorts an array using the Quick Sort divide-and-conquer algorithm.

    Args:
        data: A list of integers to sort.

    Returns:
        A new sorted list containing all elements.
    \"\"\"
    # Base case: arrays with 0 or 1 element are already sorted
    if len(data) <= 1:
        return data

    # Select the pivot element
    pivot = data[len(data) // 2]
    # Partition elements into sublists
    left = [item for item in data if item < pivot]
    middle = [item for item in data if item == pivot]
    right = [item for item in data if item > pivot]

    # Recursively sort and combine results
    result = quick_sort(left) + middle + quick_sort(right)
    return result

# Example usage:
if __name__ == "__main__":
    test_data = [3, 6, 8, 10, 1, 2, 1]
    sorted_data = quick_sort(test_data)
    print(f"Sorted output: {sorted_data}")
""",
    # 2. Binary search AI style
    """from typing import List, Optional

def binary_search(data: List[int], target: int) -> Optional[int]:
    \"\"\"
    Performs binary search on a sorted list to find the target element index.

    Args:
        data: Sorted list of integers.
        target: The value to search for.

    Returns:
        The integer index of target if found, otherwise None.
    \"\"\"
    # 1. Initialize low and high pointers
    low: int = 0
    high: int = len(data) - 1

    # 2. Loop while the search window is valid
    while low <= high:
        # Calculate middle index
        mid: int = (low + high) // 2
        mid_val: int = data[mid]

        # Check if target is at mid
        if mid_val == target:
            return mid
        elif mid_val < target:
            low = mid + 1
        else:
            high = mid - 1

    # 3. Return None if not found
    return None

# Example usage:
if __name__ == '__main__':
    sample_list = [10, 20, 30, 40, 50]
    result = binary_search(sample_list, 30)
    print(f"Found at: {result}")
""",
    # 3. Path normalize utility AI style
    """import os
from typing import Optional

def normalize_file_path(file_path: str, base_directory: Optional[str] = None) -> str:
    \"\"\"
    Helper function to normalize and expand a given filesystem path.

    Args:
        file_path: The raw path string to normalize.
        base_directory: Optional parent base directory to resolve against.

    Returns:
        The normalized absolute or relative file path string.
    \"\"\"
    try:
        # Step 1: Expand user home directory
        expanded_path: str = os.path.expanduser(file_path)

        # Step 2: Combine with base directory if needed
        if base_directory and not os.path.isabs(expanded_path):
            combined_path = os.path.join(base_directory, expanded_path)
        else:
            combined_path = expanded_path

        # Step 3: Return normalized path result
        result: str = os.path.normpath(combined_path)
        return result
    except Exception as e:
        # Handle unexpected path parsing error
        print(f"Error normalizing path: {e}")
        return file_path
""",
    # 4. Memoize decorator AI style
    """import functools
from typing import Callable, Any, Dict, Tuple

def memoize_decorator(target_function: Callable) -> Callable:
    \"\"\"
    A decorator that caches function results based on arguments.

    Args:
        target_function: The callable function to memoize.

    Returns:
        The wrapped callable with caching functionality.
    \"\"\"
    # Cache storage dictionary
    cache_store: Dict[Tuple[Any, ...], Any] = {}

    @functools.wraps(target_function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Generate cache key from arguments
        key = (args, tuple(sorted(kwargs.items())))
        
        # Check if result is already in cache
        if key in cache_store:
            return cache_store[key]

        # Calculate result and store in cache
        result = target_function(*args, **kwargs)
        cache_store[key] = result
        return result

    return wrapper
""",
    # 5. Config parser AI style
    """from typing import Dict, Any

def parse_ini_configuration(config_content: str) -> Dict[str, Dict[str, str]]:
    \"\"\"
    Parses INI-formatted text into a structured dictionary.

    Args:
        config_content: Raw string content of the INI configuration.

    Returns:
        A dictionary mapping section names to key-value settings.
    \"\"\"
    # Initialize the output configuration dictionary
    config_data: Dict[str, Dict[str, str]] = {}
    current_section: str = "DEFAULT"
    config_data[current_section] = {}

    # Iterate over lines in content
    for line in config_content.splitlines():
        trimmed_line: str = line.strip()

        # Skip empty lines or comments
        if not trimmed_line or trimmed_line.startswith(("#", ";")):
            continue

        # Check for section header
        if trimmed_line.startswith("[") and trimmed_line.endswith("]"):
            current_section = trimmed_line[1:-1].strip()
            if current_section not in config_data:
                config_data[current_section] = {}
        elif "=" in trimmed_line:
            key, val = trimmed_line.split("=", 1)
            config_data[current_section][key.strip()] = val.strip()

    return config_data
"""
]


def generate_augmented_dataset() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Extracts features from base human and AI samples and generates an augmented
    dataset with realistic perturbations to train a generalized classifier.
    """
    rows = []
    labels = []

    # 1. Base real samples
    for sample in HUMAN_CODE_SAMPLES:
        feats = AIFeatureExtractor.extract_features(sample)
        rows.append(feats)
        labels.append(0)

    for sample in AI_CODE_SAMPLES:
        feats = AIFeatureExtractor.extract_features(sample)
        rows.append(feats)
        labels.append(1)

    # 2. Augmented feature generation using Gaussian noise around distributions
    np.random.seed(42)
    feature_names = AIFeatureExtractor.FEATURE_NAMES

    # Extract means and stds for both classes
    df_base = pd.DataFrame(rows)
    df_base["label"] = labels

    human_stats = df_base[df_base["label"] == 0][feature_names]
    ai_stats = df_base[df_base["label"] == 1][feature_names]

    h_mean = human_stats.mean()
    h_std = human_stats.std().replace(0, 0.05)

    a_mean = ai_stats.mean()
    a_std = ai_stats.std().replace(0, 0.05)

    # Generate 150 synthetic human samples and 150 synthetic AI samples
    n_samples = 150
    for _ in range(n_samples):
        h_sample = {}
        for feat in feature_names:
            val = float(np.random.normal(h_mean[feat], h_std[feat]))
            if "score" in feat or "ratio" in feat or "density" in feat or "regularity" in feat or "consistency" in feat:
                val = max(0.0, min(1.0, val))
            else:
                val = max(0.0, val)
            h_sample[feat] = round(val, 4)
        rows.append(h_sample)
        labels.append(0)

    for _ in range(n_samples):
        a_sample = {}
        for feat in feature_names:
            val = float(np.random.normal(a_mean[feat], a_std[feat]))
            if "score" in feat or "ratio" in feat or "density" in feat or "regularity" in feat or "consistency" in feat:
                val = max(0.0, min(1.0, val))
            else:
                val = max(0.0, val)
            a_sample[feat] = round(val, 4)
        rows.append(a_sample)
        labels.append(1)

    X = pd.DataFrame(rows)[feature_names]
    y = pd.Series(labels)
    return X, y

# Troubleshoot 005: NameError Free Variable Scoping

## Context & Phenomenon
During the implementation of Ticket `005-hierarchical-l1-l2-l3-remote-preview-list-viewer`, a Python `NameError` crash occurred upon running the TUI application `list_viewer.py`.
- **Traceback Fragment:** `NameError: free variable '_policy_cache' referenced before assignment in enclosing scope`
- **Location:** `src/arti_ops/cli/list_viewer.py:40` inside the closure function `get_missing_pages()`.

## Root Cause Analysis
In Python, when an inner nested function (closure) references an immutable or locally bounded structure that is evaluated downstream within the outer enclosing function scope, the Python interpreter identifies it as a bound local space.
However, during the sequential execution:
1. `get_missing_pages` function definition is bound in memory.
2. `get_missing_pages("rules")` is executed, immediately attempting to evaluate `_policy_cache`.
3. `_policy_cache` was initialized strictly 100 lines below the original invocation point physically.
Thus, when line 40 was executed, `_policy_cache` hadn't been bound yet in the enclosing execution sequence context.

## Resolution
The variable initialization was physically hoisted up to the very beginning of the `run_list_viewer` function, immediately after parameter ingestion and before the closure definitions.
```python
    # UI 데이터 수집 후 즉시 변수 컨텍스트 조기 할당 (Hoisting 방어)
    _policy_cache = policy_cache if policy_cache is not None else PolicyCache.__new__(PolicyCache)

    def get_missing_pages(folder_name):
        ...
```

## Architectural Takeaway
When developing inside `run_interactive_loop` or massive inline UI state-managed blocks (like `prompt_toolkit`), closures are frequently utilized as event consumers (`kb.add("x")` handlers) and helper hooks. We must strictly ensure that any shared outer state parameters accessed by these closures are assigned robust defaults BEFORE invoking ANY downstream data collection helpers in the same script structure.

# Text-to-SQL demo episode (structured generation, custom comparator)

Shows two things the Banking77 demo does not:

1. **`task_kind: structured`** -- the policy switches to the 2pp margin and
   warns about label-budget economics (small budgets bought nothing on the
   paper's text-to-SQL task).
2. **`comparator: comparator.py::compare`** -- plug in your own correctness
   function. The default here is normalized string match; replace `compare`
   with execution against your database for a real execution-accuracy
   metric. The framework never needs to change.

Spider data preparation is task-specific; see the paper's released harness
for a full SQLite execution comparator.

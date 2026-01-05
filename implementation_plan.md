# Task: Refactor and Fix Titi

## Status
- [x] Refactor `titi/exec.py` to be a "dumb parameter passing" module.
- [x] Rename `EXEC` to `Exec` and thread the functor.
- [x] Move `trace_output` logic to `ar_map`.
- [x] Pass `sys.executable` to `Exec`.
- [x] Thread `asyncio` loop.
- [x] Use PEP 695 type aliases.
- [ ] Merge/inline unnecessary functions in `interactive.py`.
- [ ] Fix failing tests in `tests/test_harness.py`.
- [ ] Update `tests/xargs-curry.log`.
- [ ] Run all examples in README files and verify.

## Plan
1.  **Refactor `interactive.py`**: Inline `async_command_main` and `async_titi_main` if they are just wrappers, or consolidate them into a more flexible `run` function.
2.  **Update `__main__.py`**: Adjust calls to the consolidated functions in `interactive.py`.
3.  **Fix IO handling**: Ensure that merged results have appropriate newlines or that `echo` behavior is consistent.
4.  **Update log files**: Specifically `xargs-curry.log` to match the "dumb parameter passing" results.
5.  **Final verification**: Run `pytest tests/test_harness.py` and manually check README examples.

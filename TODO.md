```py
label: QLabel = new(enabled="function_name OR binding name - how to differentiate? or Callable ... let's use () calling parens")
```

Ideally can we check if enabled= has a setEnabled which accepts a bool as the first arg? and in those scenarios setup BINDINGS to toggle that?

so before that let's make this work, `bind="whatever.upper()"` and `len(whatever)`

======

Overview of TODOs, high-level ...

## Port over from V1

- [ ] E2E tests, I think for App stuff mostly? skip by default.
- [x] async stuff
- [x] bind= using complex evaluations w/ reactive updates
- [ ] undo/redo (meh, forget it)
- [ ] serialization (meh, forget it)
- [ ] translation

## New

- [x] boolean= predicate expression or function reference or reactive binding, the expression also reacts to updates ...

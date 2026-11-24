# Leeravontuur structuur: a map of the whole code

This folder explains every file of the project, down to every function and who calls it. It exists so that the
code can be inspected in full detail without reading it all. It reflects `main` at commit `6f33a3b` (merge of
pull request #64, version 0.28.0).

## What is in here

| File | What |
|---|---|
| `<repo path>.json` | One counterpart per explained file, at the same relative path plus `.json`. Example: `leeravontuur/kern/klad.py` is explained in `leeravontuur structuur/leeravontuur/kern/klad.py.json`. |
| `index.json` | Every file of the repo in one list: kind, layer, size, one-sentence purpose, what it imports and who imports it, the path of its counterpart. The images are listed as "generated, not explained". |
| `dynamic-dispatch.json` | The places where code is called through a table, a registry or `getattr`, which cannot be followed statically. |
| `schema.json` | The standard every counterpart follows (JSON Schema, draft-07). |

**What is explained (227 files):** all Python (95 program files, 37 test files), the 49 JSON data files, the 39
markdown files, and the scripts and configuration. **Not explained:** the 132 handbook screenshots (SVG), 1 PNG and
`LICENSE`.

## How to read a counterpart

Every counterpart starts with the same keys: `path`, `kind` (python, test, json, markdown, script, config), `layer`,
`lines`, `source_sha256`, `purpose` (one sentence) and `details` (a few sentences). Then, by kind:

- **python / test:** `imports` and `imported_by` (which files, resolved to paths); `constants`; `registries`;
  `classes` (each with `bases`, `attributes`, `instantiated_by` and its `methods`); `functions`.
- **Every function** has `lines`, `params`, `decorators`, `docstring` (the first paragraph of the one in the code,
  mostly Dutch), `explanation` (English), and its calls:
  - `calls`: functions and methods of this project it calls, as `<path>::<qualified name>`, with line numbers.
    Calling a class points at its `__init__`.
  - `called_by`: the reverse, `<path>::<qualified name>`. Tests count as callers.
  - `unresolved_calls`: a method called on an object whose type is not known statically (`obj.maak(...)`). The
    project methods with that name are listed as `candidates` (only when there are 6 or fewer).
  - `external_calls`: the built-ins, standard library and third-party callables it uses.
  - `dynamic`: calls through `getattr` with a computed name, or through a table (`REGISTRY[key](...)`).
- **json:** `keys`, `shape` (the structure with types), `read_by` (the code that loads it), `field_notes`.
- **markdown:** `summary`, `headings`, `links`, `referenced_by`, `words`.

Qualified names: `Class.method` for a method, `outer.inner` for a function defined inside another function.
Module-level code that runs when the file is imported (registrations, class bodies, `__main__` blocks) is under
`module_calls`.

## Limits (read these before trusting a call graph)

- **Explanations are Claude's reading of the code.** They were written by hand after reading each file and can
  contain mistakes. The facts (line numbers, parameters, imports, calls) come from the Python syntax tree, not from
  memory; the explanations do not.
- **Test explanations are shorter.** They were written from the test names and the code of each test and say what a test checks; they do not list every assertion.
- **A call through a table, a registry or `getattr` is not a call edge.** Examples: `INVOER[v.invoer](v, o)`, the
  `ONDERWERPEN` catalogue, `getattr(self, "_" + soort)`. They are listed in `dynamic-dispatch.json`, and the
  explanation of the function says where they lead.
- **Reading an attribute is not a call.** A property that is only read (`obj.tips_op`) shows no `called_by`.
- **Method calls on objects of unknown type** are listed as `unresolved_calls` with candidates instead of being
  guessed.
- **The map is a snapshot.** It is not updated by a script or checked by a test. It is made again when the father
  asks. `source_sha256` says which version of each file was explained.

## Words from the code you will meet

| Word | Meaning |
|---|---|
| the father ("de vader") | The parent who decides everything the child or parent sees. |
| kern | The core: all logic and storage, no screens. |
| terminal | The screens and input (curses). |
| venster | Separate-process windows (tkinter), now only the clock window. |
| inhoud | Content data: learning lines, word-problem worlds, avatar parts (JSON). |
| leerlijn | A learning line: parameters per school year for one skill (`inhoud/leerlijnen/<id>.json`). |
| vaardigheid, onderwerp | A skill (stored id) and the exercise class that makes its questions. |
| vak, domein | Subject (Wiskunde, Taal) and area within it (Breuken, Meetkunde). |
| Oefenaar | The one screen that plays every exercise: read, scratch pad, answer. |
| klad | The scratch pad: lines of calculation that are checked as the child types. |
| vraag, sessie | One question; a run of answered questions that is stored. |
| spiekbrief | The cheat sheet shown after the last hint. |
| herhaalbak | The repeat bin: questions to practise again. |
| reeks | A run of questions (usually 10). |
| tip | A hint (F1). |
| denkfout | A recognised thinking error, with its own hint. |
| invoer-object | A class that draws and handles one kind of answer (grid, fraction bar, clock hands, ...). |
| vak (panel) | A bordered panel of the newer screen layout, behind `LEERAVONTUUR_BETA=1`. |
| werkbestand | A short plan in `werk/` that comes before building. |

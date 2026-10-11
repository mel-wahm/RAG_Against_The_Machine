# The Atlas Project: A Comprehensive Markdown Test Document

> **Purpose:** This document is deliberately varied and fairly long. Use it to test a Markdown chunker against headings, paragraphs, lists, code blocks, tables, links, blockquotes, inline formatting, HTML, and edge cases.
>
> It is fictional technical documentation. The examples are illustrative and are not intended to describe a real service.

## 1. Project Overview

Atlas is a fictional document-processing service that collects source files, normalizes their contents, splits them into chunks, and prepares those chunks for search. Its design emphasizes predictable behavior, traceable source locations, and small components that can be tested independently.

The service accepts Markdown, plain-text, and Python files. Each file type has different structural clues. Python code can be analyzed with an abstract syntax tree, while Markdown relies primarily on headings, block boundaries, and inline syntax. Plain text may have no explicit structure at all, so its chunking strategy often depends on paragraphs and length.

The project uses a staged pipeline:

1. **Discovery** finds candidate files.
2. **Extraction** reads file contents.
3. **Chunking** divides the contents into useful pieces.
4. **Index preparation** attaches metadata and creates representations suitable for searching.
5. **Retrieval** selects relevant pieces for a query.
6. **Answer construction** uses retrieved context to prepare a response.

The stages are separated so that each can be tested without requiring the entire application to run. For example, a chunker test should not need a vector database, and a retrieval test should not need to rescan every source directory.

### 1.1 Design Principles

Atlas follows several design principles.

- **Preserve meaning:** avoid cutting a sentence, code block, or list when a better boundary is available nearby.
- **Respect limits:** aim for a configurable maximum chunk size while defining explicit behavior for unusually long indivisible elements.
- **Keep provenance:** each chunk should retain enough metadata to identify its source file and position.
- **Make behavior testable:** given the same input and settings, the chunker should produce the same output.
- **Prefer clear rules:** a simple strategy with documented trade-offs is easier to debug than a complicated strategy with hidden behavior.

A chunker cannot guarantee that every chunk is equally meaningful. A short heading may make little sense alone, and a long table may be difficult to split without losing the relationship between its columns and rows. The goal is to preserve useful context while keeping the result manageable.

### 1.2 Terminology

| Term | Meaning |
|---|---|
| Source document | The original file being processed |
| Block | A structural Markdown element, such as a paragraph, heading, list, or fenced code block |
| Chunk | A section of source content emitted by a chunker |
| Span | A pair of offsets identifying a region of the source text |
| Metadata | Information about a chunk, such as its path or heading hierarchy |
| Overlap | Content repeated between neighboring chunks to preserve context |
| Embedding | A numerical representation of content produced by an embedding model |
| Retrieval | The process of selecting content relevant to a query |

## 2. Installation and Configuration

Atlas requires a supported Python version and a virtual environment. The exact dependency list depends on which optional features are enabled. The Markdown chunker itself should ideally remain independent of any embedding model or database.

A minimal configuration might look like this:

```toml
[project]
name = "atlas-document-tools"
version = "0.1.0"
requires-python = ">=3.12"

[tool.atlas.chunking]
max_chunk_size = 1800
overlap = 120
preserve_headings = true
```

The configuration above is an example, not a promise that every option is implemented. A robust application should validate configuration values at startup and report which settings are supported.

### 2.1 Configuration Rules

The maximum chunk size must be a positive integer. A value of zero does not allow useful chunks, and a negative value has no sensible interpretation for a length limit.

Overlap should be zero or a positive integer. It should normally be smaller than the maximum chunk size. If overlap is too large, neighboring chunks may contain almost the same text, wasting storage and making retrieval results redundant.

Unknown configuration keys should either be rejected with a clear error or handled according to an explicitly documented forward-compatibility policy. Silently ignoring misspelled keys can make debugging unnecessarily difficult.

### 2.2 Example Environment Variables

```bash
export ATLAS_DATA_DIR="./data"
export ATLAS_MAX_CHUNK_SIZE="1800"
export ATLAS_LOG_LEVEL="INFO"
```

Environment variables are strings. If a setting represents an integer, the application must convert it and handle invalid values. For instance, `ATLAS_MAX_CHUNK_SIZE="many"` should result in a useful configuration error rather than an obscure exception much later in the pipeline.

## 3. How Markdown Is Structured

Markdown is a lightweight markup language. It uses plain characters to indicate structure, but those characters do not all have the same role. A heading introduces a section, a blank line separates many block elements, and a fence marks the beginning and end of a code block.

Consider this small document:

```markdown
# Account Service

The account service handles user records.

## Login

Users provide a username and password.

```python
def login(username, password):
    return authenticate(username, password)
```
```

The outer document has a level-one heading, a paragraph, a level-two heading, another paragraph, and a fenced code block. A Markdown chunker should understand enough of these boundaries to avoid splitting them carelessly.

### 3.1 ATX Headings

ATX headings use one to six hash marks:

```markdown
# Level One
## Level Two
### Level Three
#### Level Four
##### Level Five
###### Level Six
```

The number of hash marks indicates the heading level. In a well-structured document, a level-three heading usually belongs beneath a level-two heading, although real-world Markdown may skip levels or use them inconsistently.

A heading can be valuable metadata. A chunk under `## Installation` and `### Linux` can carry the heading path `Installation > Linux`. This helps a retriever distinguish identical words used in different parts of a document.

### 3.2 Setext Headings

Markdown also supports Setext-style headings:

```markdown
A Primary Section
=================

A Secondary Section
-------------------
```

The underline determines the heading level. A chunker that only searches for lines beginning with `#` will miss these headings.

Setext syntax can be ambiguous when a line of equals signs or hyphens appears in another context. Parsing Markdown correctly requires considering the surrounding lines rather than treating every matching character sequence as a heading.

### 3.3 Paragraphs and Soft Line Breaks

A paragraph may contain several physical lines:

```markdown
This is one paragraph. It begins here
and continues on the next source line.
The line breaks do not necessarily create
separate paragraphs when rendered.
```

A blank line normally separates paragraphs. A single newline inside a paragraph is often rendered as a space, depending on the Markdown renderer.

A chunker that splits at every newline may create fragments that are too small. A chunker that joins the entire document into one string may lose the natural paragraph boundaries that are useful for retrieval.

Two spaces at the end of a line or a backslash before a newline can indicate a hard line break in common Markdown implementations:

```markdown
First line with a hard break.  
Second visible line.

First line with another hard break.\
Second visible line.
```

These cases are useful for testing whether a parser distinguishes source lines from rendered paragraphs.

## 4. Lists and Nested Structures

Lists are common in documentation and can be surprisingly awkward to split.

### 4.1 Unordered Lists

The following markers are commonly used for unordered lists:

```markdown
- First item
- Second item
- Third item
  - Nested item A
  - Nested item B
    - A deeper item
```

A list is more than a set of unrelated lines. The indentation communicates relationships between items. If a chunker separates a nested item from its parent, some of that relationship may become unclear.

Different marker styles are also valid:

```markdown
* Item using an asterisk
* Another asterisk item

+ Item using a plus sign
+ Another plus item
```

A parser may normalize these forms internally, but a source-preserving chunker should not accidentally rewrite the original text unless normalization is an explicit goal.

### 4.2 Ordered Lists

```markdown
1. Create a project directory.
2. Add a configuration file.
3. Install the dependencies.
4. Run the tests.
```

Ordered lists may use numbers other than one at the start of each item:

```markdown
3. Third item in the original numbering.
4. Fourth item in the original numbering.
5. Fifth item in the original numbering.
```

Some renderers renumber such lists when displaying them. A chunker that stores original source offsets should preserve the source numbering rather than silently rewriting it.

### 4.3 Lists with Multiple Paragraphs

```markdown
1. **Read the configuration.**

   Load the file and validate its fields before starting the application.

   A validation failure should identify the field that caused the problem.

2. **Prepare the document.**

   Normalize line endings and preserve the original source separately if exact offsets are required.

3. **Emit chunks.**

   Attach source metadata to each emitted chunk.
```

A single list item can contain several paragraphs. The continuation paragraphs are indented so that they belong to the item. A simplistic splitter might incorrectly treat each paragraph as an independent block.

### 4.4 Task Lists

Task lists are a common Markdown extension:

```markdown
- [x] Define the input model.
- [x] Implement file discovery.
- [ ] Add Markdown chunking.
- [ ] Test nested lists.
- [ ] Document oversized-block behavior.
```

The checked and unchecked boxes are not part of the core historical Markdown specification, but many Markdown platforms support them. Tests should state which Markdown dialect the chunker intends to support.

## 5. Fenced Code Blocks

Fenced code blocks can contain arbitrary source text. A common form uses three backticks:

````markdown
```python
def calculate_total(values):
    return sum(values)
```
````

The language identifier, such as `python`, is usually a hint for syntax highlighting. It may be useful metadata, but it should not be assumed to be a complete or valid language name.

Tildes can also be used as fences:

```~~~text
This block uses a tilde fence.
The fence marker is not a backtick.
~~~```

Fence length matters. If a block starts with four backticks, a shorter sequence of three backticks inside the block should not necessarily close it.

````markdown
````markdown
Here is an example that contains a shorter fence:

```python
print("This is still inside the outer example")
```

The outer fence uses four backticks.
````
````

A Markdown chunker should avoid interpreting Markdown-looking content inside a fenced code block as actual document structure. For example, `# this is a comment` inside Python code is not a Markdown heading.

### 5.1 Code Blocks Without Language Labels

```
A plain fenced block may have no language identifier.

It can contain several lines of output:
status: ready
items: 12
warnings: 0
```

Not every code block is source code. Documentation often includes command output, configuration fragments, logs, request examples, and error messages.

### 5.2 Indented Code Blocks

Some Markdown dialects recognize code blocks indented by four spaces or one tab:

    def legacy_example():
        return "indented code"

A chunker that only recognizes fenced blocks may fail to preserve these as a single block. Whether indented code must be supported depends on the parser and Markdown dialect selected for the project.

## 6. Tables

Tables are widely used in technical documentation, even though the syntax is an extension supported by many Markdown renderers.

| Status | Meaning | Suggested action |
|---|---|---|
| `200` | The operation succeeded | Read the response |
| `400` | The request was invalid | Check the submitted fields |
| `401` | Authentication is required | Provide valid credentials |
| `403` | The operation is forbidden | Check the caller's permissions |
| `404` | The resource was not found | Verify the identifier |
| `429` | The request rate is too high | Retry according to the policy |
| `500` | An internal error occurred | Inspect service logs |

The separator row may contain alignment markers:

| Left aligned | Center aligned | Right aligned |
|:---|:---:|---:|
| alpha | beta | 10 |
| gamma | delta | 200 |
| epsilon | zeta | 3000 |

A table's header gives meaning to its cells. If a large table must be split, repeating the header in each chunk can improve readability. However, doing so means that the chunk's text is not simply a contiguous slice of the original source.

Tables also contain escaped pipes:

| Expression | Meaning |
|---|---|
| `a \| b` | A literal pipe inside a cell |
| `x < y` | A comparison |
| `left & right` | Two values joined by an ampersand |

The pipe inside a code span should not necessarily be interpreted as a column separator. Naive splitting on every pipe character will mishandle some valid tables.

## 7. Links, Images, and Reference Definitions

### 7.1 Inline Links

Markdown links usually follow this form:

```markdown
[Project documentation](https://example.com/docs)
```

A link may include a title:

```markdown
[API reference](https://example.com/api "API reference title")
```

Autolinks are another form:

```markdown
<https://example.com/status>
<support@example.com>
```

When preparing content for retrieval, it is often useful to preserve both the link text and its destination. The visible text may explain the purpose of a link, while the destination identifies the resource.

### 7.2 Reference-Style Links

A link can refer to a definition elsewhere in the document:

```markdown
Read the [installation guide][install-guide] before running the project.

The [API guide][api-guide] explains the available operations.

[install-guide]: https://example.com/install "Installation"
[api-guide]: https://example.com/api "API"
```

Definitions may be far from the paragraph that uses them. A chunk containing only the first paragraph may retain the reference label but omit its definition. Depending on the use case, a chunker may preserve definitions as separate blocks, attach resolved link metadata, or include relevant definitions with their uses.

### 7.3 Images

```markdown
![A placeholder diagram showing a document pipeline](https://example.com/pipeline.png)
```

Image syntax contains alternative text, which can be meaningful even if the image itself is not downloaded. A text-only indexing pipeline should preserve the alt text and, when useful, the image URL.

Reference-style images are also possible:

```markdown
![Pipeline diagram][pipeline-image]

[pipeline-image]: https://example.com/pipeline.png "Pipeline diagram"
```

The description and reference definition may be separated, so tests should include both inline and reference-style images.

## 8. Inline Formatting and Special Characters

Markdown has several forms of inline formatting.

This paragraph contains **bold text**, *italic text*, ***bold italic text***, and ~~strikethrough text~~. It also contains `inline code`, a literal asterisk \*, and escaped brackets \[like these\].

Inline code is particularly important because its contents should not normally be parsed as Markdown syntax. For example, the text `# not a heading` is inline code, not a heading.

A code span may contain a backtick by using a longer delimiter:

```markdown
Use `` `value` `` to show a backtick inside inline code.
```

Markdown implementations differ in their support for strikethrough, underline, and other extensions. A chunker should not assume every renderer interprets every extension identically.

### 8.1 HTML Inside Markdown

Markdown documents may contain raw HTML:

```html
<details>
  <summary>Show additional information</summary>
  <p>This paragraph is hidden until the section is expanded.</p>
</details>
```

Another example is a simple HTML table:

<table>
  <thead>
    <tr><th>Key</th><th>Value</th></tr>
  </thead>
  <tbody>
    <tr><td>environment</td><td>testing</td></tr>
    <tr><td>region</td><td>north</td></tr>
  </tbody>
</table>

Raw HTML support varies by renderer and security policy. If HTML is allowed, a chunker should decide whether to treat a complete HTML element as a block or process its text and tags separately.

## 9. Blockquotes and Admonitions

A standard blockquote begins with a greater-than sign:

> This is a short quotation.
>
> It contains two paragraphs.

Blockquotes can contain other Markdown structures:

> ## A heading inside a quotation
>
> This paragraph belongs to the blockquote.
>
> - Quoted item one
> - Quoted item two
>
> ```python
> quoted_value = 7
> ```

A blockquote may span several lines. Removing the quote markers can be useful for display, but it changes the source text and may affect offsets.

Some documentation systems use admonition syntax:

```markdown
!!! warning "Data loss"
    Back up the original file before running a destructive operation.
    Confirm the destination before continuing.
```

Other systems use a blockquote extension:

```markdown
> [!NOTE]
> This operation only changes the local index.
>
> The source documents remain unchanged.
```

These forms are extensions rather than universally supported core Markdown syntax. A general-purpose chunker may preserve them as ordinary blockquotes or recognize them as specialized blocks.

## 10. Horizontal Rules and Thematic Breaks

These are common horizontal-rule forms:

```markdown
---
***
___
```

A thematic break separates sections visually. However, a line containing hyphens may also appear in a Setext heading or a list. The surrounding context matters.

A test document should include thematic breaks both between ordinary paragraphs and near other structures. Otherwise, a simplistic parser may pass the easy cases while failing when the syntax is ambiguous.

Paragraph before the break.

---

Paragraph after the break.

## 11. Heading Hierarchy and Context Preservation

Consider the following hierarchy:

# Deployment

Deployment instructions differ by environment.

## Local Development

Local development uses a lightweight configuration.

### Start the Service

Run the service from the repository root.

### Verify the Service

Check the health endpoint and inspect the logs.

## Production

Production deployment requires additional validation.

### Configuration

Production credentials must be provided through the deployment environment rather than committed to the repository.

### Monitoring

Monitor error rates, request latency, and resource consumption after a release.

A chunk containing only the sentence about the health endpoint may be understandable to a person who has read the preceding headings. A retriever, however, may retrieve that sentence without the surrounding section.

One way to address this is to store heading metadata:

```text
heading_path: Deployment > Local Development > Verify the Service
```

Another approach is to prepend the heading path to the chunk's searchable text. This may improve retrieval, but it also changes the indexed text and increases its size. The original source should remain available separately if exact reconstruction is important.

### 11.1 Duplicate Headings

## Configuration

The application reads configuration from a file.

## Configuration

The command-line interface accepts configuration overrides.

Duplicate headings are legal. A heading path containing only `Configuration` is not unique. A chunker may need a broader hierarchy, a source location, or a section identifier to distinguish the two sections.

### 11.2 Skipped Heading Levels

# Reference

### Internal API

The document jumps directly from level one to level three. This may be poor editorial structure, but it is still input that a robust chunker can encounter.

The chunker should not crash merely because heading levels are skipped. It should define a consistent rule for building heading paths when the source hierarchy is irregular.

## 12. Long-Form Technical Explanation

Document chunking involves several competing goals. Small chunks make retrieval more precise because each chunk tends to discuss a limited topic. Large chunks retain more context, which can help a language model understand relationships between concepts. Neither extreme is universally best.

Suppose a user asks how a configuration value flows from an environment variable into a service object. A tiny chunk containing only the environment variable name may match the query but fail to explain where the value goes. A very large chunk containing the entire configuration subsystem may include the answer but bury it among unrelated material.

The best chunk size depends on the source material, the retrieval method, the embedding model, and the kinds of questions users ask. Character count is a convenient approximation, but many language models process text in tokens. Characters and tokens do not have a fixed one-to-one relationship. Source code, punctuation, identifiers, and non-English text can tokenize differently.

A practical evaluation should use representative questions and inspect the chunks that are retrieved. It should measure not only whether the correct document is found, but also whether the retrieved passage contains enough information to answer the question correctly. This can reveal failures that a simple size test cannot detect.

### 12.1 Example: A Poor Boundary

Imagine a chunker splits this paragraph after the word “because”:

> The cache must be invalidated after the schema changes because

The next chunk begins:

> old serialized records may no longer match the expected data structure.

Neither fragment is ideal on its own. A paragraph-aware chunker should normally prefer a boundary between paragraphs or sentences, provided the size constraint allows it.

### 12.2 Example: An Oversized Paragraph

Now consider a single paragraph that contains 4,000 characters and no blank lines. A paragraph-aware strategy cannot keep the paragraph intact if the configured maximum is 1,500 characters.

It needs a fallback rule. Possible choices include splitting at sentence boundaries, splitting at word boundaries, or using a fixed character window. Each choice has trade-offs. Sentence splitting can be confused by abbreviations and code fragments; word splitting may separate tightly related clauses; fixed windows are simple but may cut through sentences.

A well-designed implementation documents its fallback behavior and tests it explicitly.

## 13. Chunking Strategies Compared

| Strategy | Advantages | Limitations |
|---|---|---|
| Fixed character windows | Simple and predictable | Can cut sentences and blocks |
| Paragraph-based | Usually preserves prose units | Large paragraphs need fallback splitting |
| Heading-based | Retains section structure | Sections can become extremely large |
| Recursive block splitting | Tries several boundaries in order | More complex to implement and test |
| Token-based | Aligns with model token budgets | Requires a tokenizer and adds processing cost |
| Semantic splitting | Attempts to keep related ideas together | More expensive and less deterministic |

A recursive Markdown chunker might try the following boundaries in order:

1. Heading boundaries.
2. Blank lines between blocks.
3. Paragraph or list-item boundaries.
4. Sentence boundaries.
5. Word boundaries.
6. Character boundaries as a final fallback.

This order is only a possible design. A real implementation should decide how to treat tables, fenced code blocks, HTML elements, and nested lists before claiming to preserve all Markdown structure.

## 14. Metadata and Provenance

A chunk is more useful when it carries information about where it came from.

Possible metadata fields include:

| Field | Example | Purpose |
|---|---|---|
| `file_path` | `docs/setup.md` | Identifies the source document |
| `start_offset` | `420` | Records the starting character offset |
| `end_offset` | `1120` | Records the ending character offset |
| `heading_path` | `Setup > Linux` | Preserves section context |
| `chunk_index` | `4` | Identifies the chunk's order in a document |
| `language` | `markdown` | Records the content format |

Not every project needs every field. The important thing is to distinguish source metadata from derived metadata. Character offsets refer to the original source; heading paths and embeddings may be derived from it.

If chunks overlap, two chunks may legitimately cover some of the same source positions. If headings are prepended to chunk text, the indexed text may not match a contiguous source slice. These choices should be represented clearly rather than hidden behind ambiguous offset fields.

### 14.1 A Fictional Chunk Record

```json
{
  "file_path": "docs/setup.md",
  "start_offset": 420,
  "end_offset": 1120,
  "chunk_index": 4,
  "heading_path": ["Setup", "Linux"],
  "content_type": "markdown"
}
```

This is an illustrative record. The offsets and metadata are examples, not references to actual positions in this test document.

## 15. Search and Retrieval Considerations

Indexing prepares content for future search. It does not, by itself, determine whether a search result is relevant.

A keyword search might find a chunk because it contains the exact term `authentication`. A vector search might find a chunk about signing in even if it uses different words. Hybrid retrieval combines lexical and semantic signals.

The best approach depends on the corpus. Technical documentation often contains exact identifiers, command names, error codes, and configuration keys that benefit from lexical search. Semantic search can help with paraphrased questions. Combining both can be useful, but it also introduces more parameters and evaluation work.

After retrieval, a system may rerank candidate chunks, remove duplicates, or group adjacent chunks from the same section. These are retrieval-stage decisions, not necessarily responsibilities of the Markdown chunker itself.

### 15.1 Example Search Questions

Use these questions to evaluate whether the resulting chunks retain useful context:

- How do I configure the maximum chunk size?
- What happens when a single paragraph is larger than the limit?
- Which Markdown heading syntax is supported?
- Why might a table need its header repeated?
- What metadata identifies the original source location?
- How are duplicate headings distinguished?
- What is the difference between character-based and token-based limits?
- Why might a hybrid search system be useful for technical documentation?

A useful evaluation set includes both exact terminology and paraphrased questions.

## 16. Error Handling and Robustness

Real-world documentation is not always perfectly formatted. Files may end abruptly, contain unmatched fences, use inconsistent heading levels, or include very long lines. Some may use extensions that the selected parser does not recognize.

The chunker should define how it handles malformed input. Possible policies include preserving the content as best it can, returning a structured error, or skipping the file with a diagnostic. The right policy depends on whether missing content is acceptable for the application.

An unmatched opening code fence is especially important. If the parser treats the remainder of the document as code, subsequent headings may no longer be recognized as headings. That behavior may be consistent with the chosen Markdown specification, but it should be covered by a test.

### 16.1 Robustness Checklist

- Empty input returns no chunks or a documented empty chunk.
- A document containing only whitespace is handled consistently.
- A file without a final newline is processed correctly.
- Unicode characters are preserved.
- CRLF and LF line endings are handled as intended.
- Unclosed fences do not cause an unhandled crash.
- Large tables do not cause unbounded memory use.
- Repeated headings do not overwrite each other's metadata.
- A single oversized block follows the documented fallback rule.
- Invalid configuration values produce clear errors.

## 17. Testing Strategy

Tests should cover ordinary inputs, boundary conditions, and combinations of Markdown features.

### 17.1 Basic Cases

```markdown
# Title

A short paragraph.

Another short paragraph.
```

Expected behavior should be simple: the title and paragraphs should be recognized as distinct structural blocks, subject to the chunker's grouping policy.

### 17.2 Boundary Case: Exactly at the Limit

Suppose a chunk limit is 100 characters and a candidate block is exactly 100 characters long. The implementation should have a clearly defined rule for whether this block fits. Usually, a maximum means that a size equal to the limit is accepted.

### 17.3 Boundary Case: One Character Too Large

If a block has 101 characters under a limit of 100, the chunker should invoke its fallback splitting strategy or document why that block may exceed the limit.

### 17.4 Boundary Case: Blank Lines

```markdown
First paragraph.


Second paragraph after multiple blank lines.
```

Multiple blank lines should not accidentally create empty chunks unless empty chunks are explicitly part of the design.

### 17.5 Boundary Case: Fences Inside Fences

````markdown
````markdown
Example outer block.

```python
print("inner example")
```

End of outer block.
````
````

This tests whether the parser respects fence lengths rather than closing a four-backtick block at the first three-backtick sequence.

### 17.6 Property-Based Tests

In addition to specific examples, consider properties that should hold for many generated inputs:

- Every emitted span has a start offset no greater than its end offset.
- Every span lies within the source bounds.
- Chunk ordering follows source ordering, unless a documented transformation changes it.
- No chunk exceeds the maximum unless an explicitly permitted fallback applies.
- The same input and configuration produce the same chunks.
- Metadata points to the correct source document.

Property-based tests can generate many combinations of Unicode, whitespace, fences, and headings. They are particularly useful after a basic suite of hand-written examples is already working.

## 18. Performance Notes

Markdown parsing can be performed with a dedicated parser, a line-based state machine, or a combination of both. A dedicated parser can handle syntax interactions more reliably, while a custom line-based approach can be easier to tailor to a narrow set of requirements.

The choice should reflect the desired Markdown dialect. Supporting CommonMark and popular extensions comprehensively is more work than recognizing headings, paragraphs, and fenced code blocks for a private corpus.

For a large corpus, avoid repeatedly scanning the entire document for each emitted chunk. A single pass that identifies structural blocks and records their source positions can reduce unnecessary work. Likewise, avoid copying large strings repeatedly if the chunker only needs to retain offsets and metadata.

Correctness should come before micro-optimization. A very fast chunker that silently drops code blocks or loses Unicode characters is not useful.

## 19. Open Questions for the Implementation

Before writing a Markdown chunker, decide what its contract should be.

1. Which Markdown dialect is supported?
2. Are source offsets required, or is returning chunk text enough?
3. Are headings included in the content of their following chunks?
4. Is the heading hierarchy stored as metadata?
5. Can chunks overlap?
6. Are fenced code blocks kept intact whenever possible?
7. How are large tables split?
8. What happens to a paragraph larger than the maximum?
9. Are raw HTML blocks supported?
10. Is the size limit measured in characters, bytes, or tokens?

These are not merely implementation details. They determine what downstream indexing and retrieval can rely on.

A minimal first version might support ATX headings, paragraphs, lists, fenced code blocks, and blockquotes. It could preserve source offsets and use paragraph boundaries before falling back to sentence or word boundaries. More advanced syntax could be added after tests show it is needed.

## 20. A Longer Mixed-Structure Test Section

This section deliberately alternates between different Markdown structures. It is useful for checking whether a chunker flushes or groups content at the correct boundaries.

### 20.1 First Procedure

To prepare a document, begin by identifying the source path and reading the file with a consistent encoding. Preserve the original text if source offsets will be used later. Normalize only what the application can safely normalize without invalidating those offsets.

Then inspect the document's structure. A heading introduces a section, a paragraph provides explanatory text, and a fenced code block may contain a command or example. Each of these blocks has different splitting considerations.

```bash
python -m atlas inspect ./docs/guide.md
python -m atlas chunk ./docs/guide.md --max-size 1800
```

The commands are fictional examples. They are included to test fenced blocks and should not be expected to run.

### 20.2 Decision Table

| Condition | Preferred action | Fallback |
|---|---|---|
| A block fits in the current chunk | Add the block | None |
| A block would exceed the limit | Finish the current chunk | Start a new chunk |
| A paragraph exceeds the limit | Split at a sentence boundary | Split at a word boundary |
| A fenced code block exceeds the limit | Split at a safe internal boundary | Split by lines |
| A table exceeds the limit | Split by rows and preserve the header | Use a documented generic strategy |
| A heading has no body | Attach it to nearby content | Emit it separately if necessary |

A table-driven implementation can make these policies explicit. It also gives reviewers a compact way to understand the expected behavior without reading every branch of the code.

### 20.3 A Quoted Requirement

> The chunker must preserve enough context for the retrieval system to interpret each chunk. If the maximum size conflicts with preserving an indivisible block, the implementation must follow a documented fallback policy.

This requirement is intentionally broad. It does not specify exactly how to split every block type. Those decisions belong in the implementation's design notes and tests.

### 20.4 Inline Syntax in a Dense Paragraph

A single paragraph can mix `inline_code`, **bold emphasis**, *italics*, [links](https://example.com), escaped punctuation such as \#, and identifiers such as `Chunker.max_chunk_size`. A parser should not confuse a hash inside inline code with a heading marker, nor should it assume that every bracketed phrase is a link. This dense example helps reveal whether a naive regular-expression approach mistakes inline syntax for block structure.

## 21. Glossary

**AST:** An abstract syntax tree representing the syntactic structure of a program.

**Block element:** A structural Markdown unit, such as a heading, paragraph, list, or code block.

**Chunk:** A portion of a document prepared for downstream processing or retrieval.

**Chunk boundary:** A position where one chunk ends and another begins.

**CommonMark:** A specification that defines a standardized interpretation of much of Markdown syntax.

**Embedding:** A vector representation generated from text or another input.

**Fenced code block:** A code block delimited by a sequence of backticks or tildes.

**Heading path:** A representation of the heading hierarchy leading to a given section.

**Metadata:** Descriptive information associated with a chunk, including its source path and structural context.

**Overlap:** Repeated content shared by adjacent chunks.

**Provenance:** Information that identifies the origin of a piece of content.

**Retrieval:** Selecting stored content that may help answer a query.

**Source offset:** A numeric position in the original source text.

**Token:** A unit used by a language model's tokenizer. Tokens are not equivalent to characters or words.

**Vector search:** Searching for items based on numerical vector similarity.

## 22. Final Test Matrix

Use this matrix as a quick checklist when evaluating a Markdown chunker.

| ID | Feature | Included in this document? |
|---|---|---|
| MD-01 | ATX headings | Yes |
| MD-02 | Setext headings | Yes |
| MD-03 | Paragraphs with soft line breaks | Yes |
| MD-04 | Unordered lists | Yes |
| MD-05 | Nested lists | Yes |
| MD-06 | Ordered lists | Yes |
| MD-07 | Task lists | Yes |
| MD-08 | Fenced code blocks | Yes |
| MD-09 | Tilde fences | Yes |
| MD-10 | Longer nested fences | Yes |
| MD-11 | Indented code blocks | Yes |
| MD-12 | Tables and alignment markers | Yes |
| MD-13 | Escaped pipes | Yes |
| MD-14 | Inline links and titles | Yes |
| MD-15 | Reference-style links | Yes |
| MD-16 | Images and reference images | Yes |
| MD-17 | Inline formatting and escapes | Yes |
| MD-18 | Raw HTML | Yes |
| MD-19 | Blockquotes with nested blocks | Yes |
| MD-20 | Admonition extensions | Yes |
| MD-21 | Horizontal rules | Yes |
| MD-22 | Duplicate headings | Yes |
| MD-23 | Skipped heading levels | Yes |
| MD-24 | Long paragraphs | Yes |
| MD-25 | Metadata examples | Yes |
| MD-26 | Unicode and source offsets | Mentioned |
| MD-27 | Empty documents and malformed input | Discussed as test cases |
| MD-28 | Oversized blocks | Discussed as test cases |
| MD-29 | Mixed consecutive structures | Yes |
| MD-30 | Glossary and dense prose | Yes |

## 23. Closing Notes

A good Markdown chunker should be predictable, preserve useful structure, and make its trade-offs visible. It does not need to support every extension in the first version. It does need a clearly defined scope, a reliable fallback for oversized blocks, and tests that cover the syntax actually present in the target corpus.

Start with the structures most common in your files. Inspect the resulting chunks manually. Then add tests for the cases that cause poor boundaries or lost context. This gradual approach makes it easier to tell whether each change improves retrieval quality.

The most important rule is simple: **do not assume that splitting text is the same as understanding its structure.** Markdown carries meaning through headings, nesting, fences, tables, links, and surrounding context. A useful chunker takes those signals into account without becoming unnecessarily complicated.

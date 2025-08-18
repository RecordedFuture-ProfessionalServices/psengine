## Introduction 

The Analyst Notes modules allows you to download, search, publish and fetch attachments of analyst notes. 
An analyst note is a note that is either:
- written and published by someone in your organization via the Recorded Future portal or the Recorded Future API,
- written and published by the Recorded Future Insikt team.

## Notes

When searching for multiple notes or fetching a single note by `id_`, the object returned is the same. This is different from most of the Recorded Future API behaviours where a search is a portion of the full object. Which means that you don't have to search for all the new notes and fetch them one by one to get the full details. 

When searching for multiple notes, the number of notes returned is not defined by the `max_results` parameter. The `max_results` defined the maximum number of references from which notes are fetched, up to 1000. Note: The number of notes returned can be lower than this limit if some of the fetched references links to the same analyst note.

## Examples

**Example 1**: Searching for the last day of analyst notes, downloading and saving the attachments if present.
```python 
--8<-- "docs/examples/analyst_notes/save_attachment.py"
```

**Example 2**: Searching for the last day of analyst notes, downloading and saving the markdown representation of the note.

Similarly to the previous example, you can generate the markdown of an analyst note calling the `markdown` method defined for the `AnalystNote` object:
```python

--8<-- "docs/examples/analyst_notes/save_markdown.py"
```


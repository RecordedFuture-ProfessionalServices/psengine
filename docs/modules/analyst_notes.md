## Introduction

The `AnalystNoteMgr` class of the `analyst_notes` module allows you to download, search, publish, and fetch attachments of analyst notes.
An analyst note is a note that is either:

- written and published by someone in your organization via the Recorded Future portal or the Recorded Future API,
- written and published by the [Recorded Future Insikt Team](https://www.recordedfuture.com/research/insikt-group).

See the [**API Reference**](../api/analyst_notes/note_mgr.md) for internal details of the module.

## Notes

- When searching for multiple notes or fetching a single note by `id_`, the object returned is the same. This is different from most Recorded Future API behaviors, where a search is a portion of the full object. This means you don't have to search for all the new notes and fetch them one by one to get the full details.
- When searching for multiple notes, the number of notes returned is not defined by the `max_results` parameter. The `max_results` defines the maximum number of references from which notes are fetched, up to 1000. Note: The number of notes returned can be lower than this limit if some of the fetched references link to the same analyst note.

## Examples

{! modules/_includes/examples_warning.md !}

#### Search for analyst notes from the last day and save them as markdown

Similarly to the previous example, you can generate the markdown of an analyst note by calling the `markdown` method defined for the `AnalystNote` object.
In this example, we set `max_results` to `2` for a shorter output, since we are printing the markdown to the console.

To run this example, first add the `rich` package to your virtual environment:

```bash
pip install rich
```

After that, you can run it and see the markdown being written in the terminal and saved in the `attachments` directory.

```python
--8<-- "docs/examples/analyst_notes/example_2.py"
```

The `markdown` method accepts different arguments, such as `diamond_model`, to add the diamond model information to the markdown, if present. For more information, see the [**API Reference**](../api/analyst_notes/note.md).

#### Search for analyst notes from the last day and save their attachments

The `fetch_attachment` method returns a tuple with the attachment content and extension. If the note does not contain an attachment, it returns empty content and extension.
To limit the number of calls made to the API, check if the attribute `attachment` is present; if yes, fetch the attachment.

```python
--8<-- "docs/examples/analyst_notes/example_1.py"
```

#### Save analyst notes on Ransomware Actors and Tools published in the last year

In this example, we use the `search` method with the `topic` argument, which accepts either a string or a list of strings by topic ID. The list of topic IDs can be found in the [Analyst Note API](https://support.recordedfuture.com/hc/en-us/articles/30506669358611-Analyst-Note-API) support article. When performing a search, notes are deduplicated in case you select two or more topics and a note is tagged with both of them.

The `save_note` method can be used to save the note as JSON.

```python
--8<-- "docs/examples/analyst_notes/example_3.py"
```

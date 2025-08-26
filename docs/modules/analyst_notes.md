## Introduction 

The `AnalystNoteMgr` class of the `analyst_notes` module allows you to download, search, publish and fetch attachments of analyst notes. 
An analyst note is a note that is either:

- written and published by someone in your organization via the Recorded Future portal or the Recorded Future API,
- written and published by the Recorded Future Insikt team.

See the [**API Reference**](../../api/analyst_notes/note_mgr) for internal details of the module.

## Notes

1. When searching for multiple notes or fetching a single note by `id_`, the object returned is the same. This is different from most of the Recorded Future API behaviours where a search is a portion of the full object. Which means that you don't have to search for all the new notes and fetch them one by one to get the full details. 
2. When searching for multiple notes, the number of notes returned is not defined by the `max_results` parameter. The `max_results` defined the maximum number of references from which notes are fetched, up to 1000. Note: The number of notes returned can be lower than this limit if some of the fetched references links to the same analyst note.

## Examples

!!! warning

    Below are some examples of usage of the `analyst_note` module. Consider adding error handling as necessary. All the errors that can be raised by each method or function are specified in the API Reference page.


#### Example 1: Searching for the last day of analyst notes, downloading and saving the attachments if present.

The `fetch_attachment` method returns a tuple with the attachment content and extension. If the note does not contain an attachment, it will return empty content and extension.
To limit the number of calls made to the API, you can check if the attribute `attachment` is present, if yes fetch the attachment. 
```python 
--8<-- "docs/examples/analyst_notes/example_1.py"
```

#### Example 2: Searching for the last day of analyst notes, downloading and saving the markdown representation of the note.

Similarly to the previous example, you can generate the markdown of an analyst note calling the `markdown` method defined for the `AnalystNote` object.
In this example we are setting `max_results` to `2` for a shorter output, since we are printing the markdown to console.

To run this example you will first need to add the `rich` package to your virtual environment:
```bash
pip install rich
```
After that you can run it and see the markdown begin written in the terminal and being saved in the `attachment` directory.
```python

--8<-- "docs/examples/analyst_notes/example_2.py"
```
The `markdown` method accept different arguments, such as `diamond_model` to add to the markdown the diamond model information, if present. For more information see the API Reference. 

#### Example 3: Downloading and save analyst notes related to Ransomware Actors and Ransomware Tools written in the last year.

In this example we use the `search` method with the `topic` argument, which accept either a string or a list of strings by topic id. The list of topic ids can be found in the [Analyst Note API](https://support.recordedfuture.com/hc/en-us/articles/30506669358611-Analyst-Note-API) support article. When performing a search, notes are getting deduplicated, in case you select two or more topics and a note is tagged with both of them.

The `save_note` method can be used to save the note as json.
```python
--8<-- "docs/examples/analyst_notes/example_3.py"
```


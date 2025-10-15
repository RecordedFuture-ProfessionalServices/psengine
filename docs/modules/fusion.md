## Introduction

The `fusion` module allows you to interact with Fusion, a Recorded Future file manager. Within fusion you can store or retrieve files that have been built by Recorded Future specifically for your enterprise.


See the [**API Reference**](../api/fusion/fusion_mgr.md) for internal details of the module.

## Notes

- There is a level of overlap with the `RisklistMgr` module, which is more suitable for retrieving risklists from Fusion in a more developer-friendly way. Use Fusion for a raw access to files, file information, or when the file that needs to be retrieved is not a risklist. See the `Risklist` page [here](./risklists.md) for some examples.


## Examples

{! modules/_includes/examples_warning.md !}

#### 1: Post a file to your fusion home

In this example you create a file, `file.txt` and write some data into it. With the `FusionMgr` you can then post the file to `/home`.

```python
--8<-- "docs/examples/fusion/example_1.py"
```

The returned value is a model which provides information on the file that has been submitted.

#### 2: Head a file

In this example you use the `head_files` method, useful for retrieving information about the file without downloading it. 

This is often used in integrations to understand if a risklist has been updated from the last fetch using the `etag` header. This header returns an hash of the file, by comparing the local file hash with the remote one, you can understand if the file on the Recorded Future side has been updated.

```python
--8<-- "docs/examples/fusion/example_2.py"
```

You can call `head_files` with a path or a list of paths. In both cases, the return value will be a list with eacelement representing a single file requested even the file was not found.

The example will output:

```
File Path: /public/risklists/default_ip_risklist.csv
File Found: True
ETag: ea738e5f7c8cae9a2b3af947e480514067f82c509c3a633ffa8ed364fb5f207c
Content Disposition: attachment; filename="default_ip_risklist.csv"
```


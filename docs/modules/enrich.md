## Introduction

The `enrich` module provides two main classes for enrichment: `LookupMgr` and `SoarMgr`.

`LookupMgr` enables you to enrich entities individually and lets you specify the type of information you want to retrieve, such as the location of an IP address.

`SoarMgr` is designed for bulk enrichment. It returns a standardized payload for all entity types, without the option to request specific details for each type. This approach is more general but allows for faster enrichment of key information like risk scores and risk rules across multiple indicators.

See the [**Lookup API Reference**](../api/enrichment/lookup_mgr.md) and the [**Soar API Reference**](../api/enrichment/soar_mgr.md) for internal details of the module.

## Notes

When using `LookupMgr` for enrichment and specifying the `fields` parameter, your chosen fields are added to the default fields for that entity type:

- For malware entities, the default fields are `entity` and `timestamp`.
- For all other entities, the default fields are `entity`, `risk`, and `timestamps`.

## Examples

{! modules/_includes/examples_warning.md !}

#### 1: Enrich a vulnerability to get the CVSSv3 information

!!! tip

    To replicate this example, the token you are using must have Vulnerability Module access. If you don't have it, change the entity to enrich to a domain or IP address, or use the example 2 as a reference.

This example uses the `LookupMgr.lookup` method to get the enrichment data of a CVE, adding the `cvssv3` field. Before printing the result, you need to check whether the CVE has been enriched. Do that with the `is_enriched` boolean attribute; if it is, print the result as JSON. Note that the result is stored under `content`, which can be an object or a string depending on the API response. If the entity has not been found, it will be a string containing a 404 message. More on this in example 4.

```python
--8 < --'docs/examples/enrich/example_1.py'
```

#### 2: Enrich multiple URLs to get the related links. Make the call multithreaded

This example demonstrates how to use the `LookupMgr.lookup_bulk` method to enrich two URLs. While `lookup_bulk` simplifies enriching multiple entities of the same type, it still makes individual API calls for each entity rather than true bulk enrichment.

In this case, the `links` field is specified, and `max_workers` controls the number of threads used here, one per call. For recommendations on thread usage, refer to the [**Guidelines**](../guidelines.md) page.

```python
--8 < --'docs/examples/enrich/example_2.py'
```

Note that the `EnrichedData` object returned by the `LookupMgr` methods, as with most of the other objects returned by PSEngine, can be printed. This returns a formatted string with basic information about the entity. Executing this code, you should see something like this:

```
EnrichedURL: http://www.example.com/1, Risk Score: 0, Last Seen: 2024-06-10 23:59:59
EnrichedURL: http://www.example.com/2, Risk Score: 0, Last Seen: 2024-06-10 23:59:59
```

#### 3: Bulk enrich a CSV file containing IP addresses and get the risk score. Save the results in a new file

This example begins by creating a `to_enrich.csv` file, which is included for demonstration purposes. In a real application, you would simply provide your list of IPs to enrich, and these setup lines of code would not be necessary. The main logic starts with initializing the `SoarMgr`.

We then read the IPs from the file into `ips_to_enrich` and use the `soar` method to enrich them. The `soar` method returns a consistent payload, even if Recorded Future has no information about a particular entity, so there is no need to check whether each entity was enriched.

Finally, we create a new file with two columns, `ip` and `score`, and save each IP address along with its corresponding score.

```python
--8 < --'docs/examples/enrich/example_3.py'
```

#### 4: Dealing with 404

The `SoarMgr.soar` method never deals with 404 errors; even if the entities given do not exist on the Recorded Future platform, it returns the same payload. The `LookupMgr.lookup` and `LookupMgr.lookup_bulk` methods handle HTTP 404 status codes by returning the `EnrichmentData` object with `content` set to a string and `is_enriched` set to `False`.

```python
--8 < --'docs/examples/enrich/example_4.py'
```

The code above will print:

```
{   
    'content': '404 received. Nothing known on this entity',
    'entity': 'CVE-999',
    'entity_type': 'vulnerability',
    'is_enriched': False
}
```

#### 5: Get all the Malware related to an IP address

In this example we enrich an IP with the `links` field. We then use the `links` method to extract a list of all the entities of type `Malware` that are related to the `Actors, Tools & TTPs` section of the `links` payload.

```python
--8 < --'docs/examples/enrich/example_5.py'
```

This will print:

```
DOPLUGS, PlugX, RedDelta PlugX
```



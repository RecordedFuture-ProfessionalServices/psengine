## Introduction

The `LookupMgr` and `SoarMgr` classes of the `enrich` module allow you to enrich entities and indicators with more contextual information.

The `LookupMgr` allows one-by-one enrichment of entities, with the possibility of specifying which type of information you want to get—for example, the location of an IP address.

The `SoarMgr` is used for bulk enrichments. The returned payload is the same for each entity type, with no possibility of getting specific information for each entity type. It is more generic but allows quicker enrichment of information like the risk score and risk rules of all the indicators.

See the [**Lookup API Reference**](../api/enrichment/lookup_mgr.md) and the [**Soar API Reference**](../api/enrichment/soar_mgr.md) for internal details of the module.

## Notes

When performing enrichment with `LookupMgr` and `fields` is specified, the fields you use are added on top of the default fields. The default fields are based on the entity type you are enriching:

- If the entity is malware, the fields are `entity` and `timestamp`.
- For all other entities, the fields are `entity`, `risk`, and `timestamps`.

## Examples

{! modules/_includes/examples_warning.md !}

#### Example 1: Enrich a vulnerability to get the CVSSv3 information

!!! tip

    To replicate this example, the token you are using must have Vulnerability Module access. If you don't have it, change the entity to enrich to a domain or IP address, or use Example 2 as a reference.

This example uses the `LookupMgr.lookup` method to get the enrichment data of the CVE, adding the `cvssv3` field. Before printing the result, you need to check whether the CVE has been enriched. Do that with the `is_enriched` boolean attribute; if it is, print the result as JSON. Note that the result is stored under `content`, which can be an object or a string depending on the API response. If the entity has not been found, it will be a string containing a 404 message. More on this in Example 4.

```python
--8<-- "docs/examples/enrich/example_1.py"
```

#### Example 2: Enrich multiple URLs to get the related links. Make the call multithreaded

This example uses the `LookupMgr.lookup_bulk` method to enrich two URLs. Note that `lookup_bulk` is not a real bulk enrichment. The real calls are still one per entity, but it is a convenient method when specific fields are needed.

Here the `links` field is specified, along with `max_workers`, which determines the number of threads to use—in this case, one per call. See the [**Guidelines**](../guidelines.md) page to check the recommended number of threads to use.

```python
--8<-- "docs/examples/enrich/example_2.py"
```

Note that the `EnrichedData` object returned by the `LookupMgr` methods, as with most of the other objects returned by PSEngine, can be printed. This returns a formatted string with some information about the entity. Executing this code, you should see something like this:

```
EnrichedURL: http://www.example.com/1, Risk Score: 0, Last Seen: 2024-06-10 23:59:59
EnrichedURL: http://www.example.com/2, Risk Score: 0, Last Seen: 2024-06-10 23:59:59
```

#### Example 3: Bulk enrich a CSV file containing IP addresses and get the risk score. Save the results in a new file

This example starts with writing `to_enrich.csv`. This is just a convenient way of allowing you to replicate the example. In a real application, these lines are not needed, as you will only need to provide the list of IPs to enrich. The core of the example starts at the `SoarMgr` initialization.

We start by reading the content of the file where our IPs are stored and saving the values in `ips_to_enrich`. Then we call the `soar` method to enrich the IPs. The `soar` method returns the same payload even if Recorded Future has no information about that specific entity; that is why there is no need to check whether the entity has been enriched.

In the last step, we create a new file with two columns, `ip` and `score`, and we save the IP address with the related score.

```python
--8<-- "docs/examples/enrich/example_3.py"
```

#### Example 4: Dealing with 404

The `SoarMgr.soar` method never deals with 404 errors; even if the entities given do not exist, it returns the same payload. The `LookupMgr.lookup` and `LookupMgr.lookup_bulk` methods handle HTTP 404 status codes by returning the `EnrichmentData` object with `content` set to a string and `is_enriched` set to `False`.

```python
--8<-- "docs/examples/enrich/example_4.py"
```

The example will print:

```
{   
    'content': '404 received. Nothing known on this entity',
    'entity': 'CVE-999',
    'entity_type': 'vulnerability',
    'is_enriched': False
}
```

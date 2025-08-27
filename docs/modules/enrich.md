## Introduction 

The `LookupMgr` and `SoarMgr` classes of the `enrich` module allows to enrich entities and indicators with more contextual information.

The `LookupMgr` allows for one by one enrichment of entities, with the possibility of specifying which type of information you want to get, for example: the location of an IP address. 

The `SoarMgr` is used for bulk enrichments, the returned payload is the same for each entity type with no possibility of getting specific information for each entity type. It is more generic but allows for quicker enrichment of information like the risk score and risk rules of all the indicators.

See the [**Lookup API Reference**](../../api/enrichment/lookup_mgr) and the [**Soar API Reference**](../../api/enrichment/soar_mgr)  for internal details of the module.

## Note

When performing enrichment with `LookupMgr` and `fields` is specified, the field you use are added on top of the default fields. The default fields are based on the entity type you are enriching:

- If the entity is a malware the fields are `entity` and `timestamp`
- For all the other entities the fields are `entity`, `risk` and `timestamps`. 

## Examples

{! modules/_includes/examples_warning.md !}

#### Example 1: Enrich a vulnerability to get the CVSSv3 information.

This example uses the `LookupMgr.lookup` method to get the enrichment data of the CVE, adding the `cvssv3` field. Before printing the result, it is needed to check if the CVE has been enriched, we do that with the `is_enriched` boolean attribute, and if it is we print the result as JSON. Note that the result is stored under the `content`, which can be an object or a string depending on the API response. If the entity has not been found it will be a string containing a 404 message.

```python 
--8<-- "docs/examples/enrich/example_1.py"
``` 

#### Example 2: Enrich multiple URLs to get the related links. Make the call multithreaded.

This example uses the `LookupMgr.lookup_bulk` method to enrich two URLs. Note that the `lookup_bulk` is **not** a real bulk enrichment. The real calls are still one per entity, but it is a convenient method when specific fields are needed. 

Here the `links` fields is specified, along with the `max_workers` which determines the number of threads to use. In this case one per call. See the [**Guidelines**](../../guidelines) page to check the recommended amount of threads to use.

```python 
--8<-- "docs/examples/enrich/example_2.py"
``` 

Note that the `EnrichedData` object returned by the `LookupMgr` methods, as per most of the other objects returned by PSEngine, can be printed. This will return a formatted string with some information around the entity. Executing this code you should see something like this:

```
EnrichedURL: http://www.example.com/1, Risk Score: 0, Last Seen: 2024-06-10 23:59:59
EnrichedURL: http://www.example.com/2, Risk Score: 0, Last Seen: 2024-06-10 23:59:59
```

#### Example 3: Bulk enrich a CSV file containing IP addresses and get the risk score. Save the results in a new file.

This example starts with writing the `to_enrich.csv`, this is just a convenient way of allowing you to replicate the example. In a real application these lines are not needed, as you will only need to provide the list of IPs to enrich. The core of the example starts at the `SoarMgr` initialization.

We start by reading the content of the file where our IPs are stored and save the values in `ips_to_enrich`. 
Then we call the `soar` method to enrich the IPs. The `soar` method returns the same payload even if Recorded Future has not information about that specific entity, that is why there is no need of checking if the entity has been enriched. 

In the last step we create a new file with two columns, `ip` and `score` and we save the IP address with the related score.
```python 
--8<-- "docs/examples/enrich/example_3.py"
``` 

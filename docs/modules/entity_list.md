## Introduction 

The `EntityListMgr` and `EntityList` classes of the `entity_lists` module allows to manage and search the Recorded Future lists. These lists can be Watch List or custom lists, they are specific to your organization and they are the core foundation of the Recorded Future alerts.

See the [**API Reference**](../api/entity_lists/entity_list_mgr.md) for internal details of the module.

## Examples

{! modules/_includes/examples_warning.md !}

#### Example 1a: Add a domain to your Domain Watch List, using the Recorded Future ID.
!!! tip
    
    In case your enterprise is a multi-organization enterprise, you will need to find the Watch List of the sub-org that you need to access. You can do that by looking at the `owner_name` attribute of each `EntityList` object.

In this example we start with the entity to add: `idn:example.com`. This syntax (`idn:`) identifies a Recorded Future entity ID for a domain (`InternetDomainName`). 

We first use the `EntityListMgr` to find the list that we want to modify. The `search` method returns always a list of `EntityList` objects if at least one Watch List is found, otherwise it will be an emtpy list. Hence why we verify with the `if` statement if the `domain_watch_list` variable has something inside. If it does we extract the first element.

The `domain_watch_list` variable is an object of `EntityList` type, which allows us to add or remove entities from that specific list. We use the `add` method to add an entity, we know the Recorded Future ID, so we can directly pass it to the `add` method. 

Once the entity has been added we check that the result of the add operation is successful and if it is, we list all the entities in the list with the `entities` method. 

```python 
--8<-- "docs/examples/entity_lists/example_1.py"
``` 

The result after the print operation will be dependent on the content of your list but it will be similar to this:

```
InternetDomainName: reddit.com, added 2025-04-08 14:49:10
InternetDomainName: example.com, added 2025-08-27 07:04:31
```

As a last instruction we print the status of the list. The `status` method will show the number of entities in the list and if the add/remove operations previously done are completed. This is because add/remove operations might take a few minutes to be processed in the backend, so the list might not be in a `ready` state yet. 

#### Example 2: Add a domain to your Domain Watch List, without using the Recorded Future ID.
!!! tip
    
    In case your enterprise is a multi-organization enterprise, you will need to find the Watch List of the sub-org that you need to access. You can do that by looking at the `owner_name` attribute of each `EntityList` object.

Similarly to example 1, in this case we do not know the Recorded Future ID of the entity, so we need to modify the `add` invocation by passing a tuple containing the name of the entity, in this case `example2.com` and the type of the entity, `InternetDomainName`. 

The method will use the `EntityMatchMgr`  from the `entity_match` module to attempt to find the id.

```python 
--8<-- "docs/examples/entity_lists/example_2.py"
```



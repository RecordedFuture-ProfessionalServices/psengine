## Introduction 

The `EntityListMgr` and `EntityList` classes of the `entity_lists` module allows to manage and search the Recorded Future lists. These lists can be Watch List or custom lists, they are specific to your organization and they are the core foundation of the Recorded Future alerts.

See the [**API Reference**](../../api/entity_lists/entity_list_mgr) for internal details of the module.

## Examples

!!! warning

    Below are some examples of usage of the `entity_lists` module. Consider adding error handling as necessary. All the errors that can be raised by each method or function are specified in the API Reference page.


#### Example 1a: Add a domain to your Domain Watch List, using the Recorded Future ID.

In this example we start with the entity to add: `idn:example.com`. This syntax (`idn:`) identifies a Recorded Future entity ID for a domain (`InternetDomainName`). 

We first use the `EntityListMgr` to find the list that we want to modify, in our specific case, we have multiple organizations under the same parent organization, hence we have multiple Domain Watch List. In your case you might have only one and the `for` loop shown is not needed. We find the list owned by the organization we want to modify and that (the `domain_watch_list` variable) will become the object that we are going to operate against.

The `domain_watch_list` variable is an object of `EntityList` type, which allows us to add or remove entities from that specific list. We use the `add` method to add an entity, we know the Recorded Future ID, so we can directly pass it to the `add` method. 

Once the entity has been added we check that the result of the add operation is succesful and if it is, we list all the entities in the list with the `entities` method. 

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

Similarly to example 1, in this case we do not know the Recoreded Future ID of the entity, so we need to modify the `add` invokation by passing a tuple containing the name of the entity, in this case `example2.com` and the type of the entity, `InternetDomainName`. 

The method will use the `EntityMatchMgr`  from the `entity_match` module to attempt to find the id.

```python 
--8<-- "docs/examples/entity_lists/example_2.py"
```



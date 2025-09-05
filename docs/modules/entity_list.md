## Introduction

The `EntityListMgr` and `EntityList` classes of the `entity_lists` module allow you to manage and search Recorded Future lists. These lists can be Watch Lists or custom lists; they are specific to your organization and are the core foundation of Recorded Future alerts.

See the [**API Reference**](../api/entity_lists/entity_list_mgr.md) for internal details of the module.

## Examples

{! modules/_includes/examples_warning.md !}

#### Example 1: Add a domain to your Domain Watch List using the Recorded Future ID

!!! tip
    In a multi-organization enterprise, you need to find the Watch List of the sub‑org you need to access. You can do that by looking at the `owner_name` attribute of each `EntityList` object.

In this example, we start with the entity to add: `idn:example.com`. This syntax (`idn:`) identifies a Recorded Future entity ID for a domain (`InternetDomainName`).

We first use the `EntityListMgr` to find the list that we want to modify. The `search` method always returns a list of `EntityList` objects if at least one Watch List is found; otherwise, it returns an empty list. Hence, we verify with an `if` statement whether the `domain_watch_list` variable has something inside. If it does, we extract the first element.

The `domain_watch_list` variable is an object of `EntityList` type, which allows us to add or remove entities from that specific list. We use the `add` method to add an entity. We know the Recorded Future ID, so we can directly pass it to the `add` method.

Once the entity has been added, we check that the result of the add operation is successful, and if it is, we list all the entities in the list with the `entities` method.

```python
--8<-- "docs/examples/entity_lists/example_1.py"
```

The result after the print operation depends on the content of your list, but it will be similar to this:

```
InternetDomainName: reddit.com, added 2025-04-08 14:49:10
InternetDomainName: example.com, added 2025-08-27 07:04:31
```

As a last instruction, we print the status of the list. The `status` method shows the number of entities in the list and whether the add/remove operations previously done are completed. This is because add/remove operations might take a few minutes to be processed in the backend, so the list might not be in a `ready` state yet.

#### Example 2: Add a domain to your Domain Watch List without using the Recorded Future ID

!!! tip
    In a multi-organization enterprise, you need to find the Watch List of the sub‑org you need to access. You can do that by looking at the `owner_name` attribute of each `EntityList` object.

Similar to Example 1, in this case we do not know the Recorded Future ID of the entity, so we modify the `add` invocation by passing a tuple containing the name of the entity—in this case, `example2.com`—and the type of the entity, `InternetDomainName`.

The method uses the `EntityMatchMgr` from the `entity_match` module to attempt to find the ID.

```python
--8<-- "docs/examples/entity_lists/example_2.py"
```

#### Example 3: Remove domains in bulk from your Domain Watch List.

!!! tip
    In a multi-organization enterprise, you need to find the Watch List of the sub‑org you need to access. You can do that by looking at the `owner_name` attribute of each `EntityList` object.

Similar to the previous examples, here we want to remove multiple domains. We use the `bulk_remove` method to do it.

```python
--8<-- "docs/examples/entity_lists/example_3.py"
```

The bulk operations return a dictionary that shows the result of each entity.

```
{'removed': [], 'unchanged': ['idn:example2.com', 'idn:reddit.com'], 'error': []}
```


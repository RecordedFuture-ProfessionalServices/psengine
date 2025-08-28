## Introduction 

The `IdentityMgr` class of the `identity` module allows to interact with the Recorded Future Identity module, to view the latest identity exposures and credential leaks happening in the domains you are monitoring.

See the [**API Reference**](../api/identity/identity_mgr.md) for internal details of the module.

## Notes

To use this module you must:

1. Have a token with Identity module permissions.
2. Have the identity module configured in your organization.
3. You might be able to view the password in clear text if your organization has been allowed to.


## Examples

{! modules/_includes/examples_warning.md !}

#### Example 1: Find the details of each recently exposed account, and report if the password has been exposed in clear text.

In this example we are searching for all workforce accounts of our organization. In this example the domain we are monitoring is `norsegods.online`. We use the `search_credentials` to find the latest credentials being exposed, with the `Email` argument to filter for only the credentials coming from accounts internal to our organization.

If we find any credential we use the `lookup_credentials` with the `subjects_login` set to the result of the `search_credentials` method. This is a convenient way of concatenating the two operations together to find all the details of each leaked identity.

We then get the needed data from the payload. Each identity might have more than one credential being leaked, so we iterate over them and and extract the information for each credential. 

Each value is added to a table for easier presentation.

To run this example you will first need to add the `rich` package to your virtual environment:
```bash
pip install rich
```

```python 
--8<-- "docs/examples/identity/example_1.py"
``` 

After running the sample code, the output would look like this:

```markdown
                                                   Discovered Credentials
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Subject                               ┃ Password Properties                                              ┃ Is Password Clear ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ example@norsegods.online              │ Letter, Number, LowerCase, AtLeast10Characters                   │         Yes       │
│ example@norsegods.online              │ Letter, Number, LowerCase, AtLeast10Characters                   │         Yes       │
│ example2@norsegods.online             │ Letter, Number, LowerCase, AtLeast10Characters                   │         Yes       │
└───────────────────────────────────────┴──────────────────────────────────────────────────────────────────┴───────────────────┘
```

#### Example 2: View the clear text password of a user that has been exposed.

In this example we check if the user `+2@norsegods.online` has a clear text password being leaked, and if yes we print it. The main purpose of this example is to show how to use the clear text password in case it has to be sent to another tool, like Active Directory, Okta etc.

The password saved in `clear_text_value` is not a plain string, if saved as is in a log file, for example with:

```python
LOG.info(cred.exposed_secret.details)
```
the log will be saved with a line looking like:

```
properties=['Letter', 'Number', 'LowerCase', 'AtLeast8Characters'] rank=None clear_text_value=ClearTextPassword('exam********') clear_text_hint='ex'
```
We did this purposefully to avoid secrets being accidentally leaked again.

To view the clear text password you need to use the `get_secret_value` method of the `clear_text_value` object.

The clear text password can be seen only if your organization has been configured to see it. 

```python 
--8<-- "docs/examples/identity/example_2.py"
``` 

#### Example 3: Search for an exposed password without sending it.

This example focuses on finding if a password has been likely exploited or not. We can use the `lookup_password` method to see:

- if the beginning of the hash of a password has been compromised
- if the full hash of the password has been compromised

We are going to use the `hash_prefix` in conjunction with the type of algorithm used to produce the hash to see if the credential has been exposed. This is an example of a one off password lookup, but the same method accepts a list of tuples like:
```python
passwords = [
    ('995bb852c775d6', 'ntlm'),
    ('8985b89acb97b011913c8b7f57e298d2', 'md5'),
]
```

The return value is always a list of `PasswordLookup`, we can safely index the first result to get the `exposure_status`.
```python 
--8<-- "docs/examples/identity/example_3.py"
``` 
Running this example should print `Common`, meaning this password hash prefix is a commonly used password.


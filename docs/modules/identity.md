## Introduction

The `IdentityMgr` class of the `identity` module allows you to interact with the Recorded Future Identity module to view the latest identity exposures and credential leaks happening in the domains you are monitoring.

See the [**API Reference**](../api/identity/identity_mgr.md) for internal details of the module.

## Notes

To use this module, you must:

- Have a token with permissions for the Identity module.
- Ensure the Identity module is configured in your organization.
- If your organization allows it, you may be able to view passwords in clear text.

## Examples

{! modules/_includes/examples_warning.md !}

#### Retrieve details of recently exposed accounts and indicate if the password is in clear text

!!! tip
    To run this example, you will need to change the domain queried by `search_credentials` to one of the domains configured in your Recorded Future enterprise.

In this example, we search for all workforce accounts within our organization, specifically monitoring the domain `norsegods.online`. The `search_credentials` function is used to find the latest exposed credentials, with the `Email` argument filtering for only those credentials associated with internal accounts.

If any credentials are found, we use the `lookup_credentials` method with `subjects_login` set to the results from `search_credentials`. This approach conveniently combines both steps to retrieve detailed information for each exposed identity.

Next, we extract the required data from the payload. Since an identity may have multiple leaked credentials, we iterate through each one to gather the relevant information.

Finally, all values are added to a table for clearer presentation.

To run this example you will first need to add the `rich` package to your virtual environment:

```bash
pip install rich
```

```python
--8<-- "docs/examples/identity/example_1.py"
```

After running the sample code, the output would look like this:

```
                                                   Discovered Credentials
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Subject                               ┃ Password Properties                                              ┃ Is Password Clear ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ example@norsegods.online              │ Letter, Number, LowerCase, AtLeast10Characters                   │         Yes       │
│ example@norsegods.online              │ Letter, Number, LowerCase, AtLeast10Characters                   │         Yes       │
│ example2@norsegods.online             │ Letter, Number, LowerCase, AtLeast10Characters                   │         Yes       │
└───────────────────────────────────────┴──────────────────────────────────────────────────────────────────┴───────────────────┘
```

#### View the clear text password of an exposed user

!!! tip
    To run this example you will need to change the email queried by `lookup_credentials` to one of the emails that has been compromised from the domains you are monitoring.
    Your token also needs access to the Identity Module.


In this example, we check whether the user `+2@norsegods.online` has a leaked clear text password, and if so, we print it. The main purpose is to demonstrate how to access and use the clear text password if it needs to be sent to another tool, such as Active Directory, Okta, etc..

The password saved in `clear_text_value` is not a plain string; if saved as is in a log file, for example with:

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

#### Search for an exposed password without sending it

!!! tip
    To run this example your token needs access to the Identity Module.

This example focuses on finding if a password has been likely exploited or not. We can use the `lookup_password` method to see:

- if the beginning of the hash of a password has been compromised
- if the full hash of the password has been compromised

We are going to use the `hash_prefix` in conjunction with the type of algorithm used to produce the hash to see if the credential has been exposed. This is an example of a one-off password lookup, but the same method accepts a list of tuples like:

```python
passwords = [
    ('995bb852c775d6', 'ntlm'),
    ('8985b89acb97b011913c8b7f57e298d2', 'md5'),
]
```

The return value is always a list of `PasswordLookup`; we can safely index the first result to get the `exposure_status`.

```python
--8<-- "docs/examples/identity/example_3.py"
```

Running this example should print `Common`, meaning this password hash prefix is a commonly used password.

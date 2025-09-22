In this section, you will find clear, easy to follow step-by-step examples demonstrating how to use each module that PSEngine has to offer.

Please note that some examples may not be fully reproducible, as they depend on your Recorded Future enterprise being properly configured, with the necessary modules enabled and appropriate permissions set on your API token. Such examples will be marked with a warning and include possible steps you may need to follow to complete them.

Also note that before running any of the examples, you need to provide a Recorded Future API token to PSEngine. You can do this in several ways:

1. Set the `RF_TOKEN` environment variable. For example, on Linux or macOS:

    ```bash
    export RF_TOKEN=<your_token>
    ```

2. Load the environment variable from a `.env` file using the [`python-dotenv`](https://pypi.org/project/python-dotenv/) module.

3. Retrieve the token from a vault and pass it as an argument to each manager class. For example:

    ```python
    from psengine.enrich import LookupMgr

    token = ... # steps to retrieve the token
    mgr = LookupMgr(rf_token=token)
    ```

For more details on the internal workings of PSEngine, refer to the [Internals](internals.md) page, which is helpful for troubleshooting or debugging.

In this section we are going to present how to utilize each module with easy to follow examples. 

Note that some examples might not be 100% reporducable since they relies on your Recorded Future enterprise being correctly set up, having the right modules and permission on the token etc. Those examples will be marked with a warning with possible steps you might need to do to complete the example.

Also note that before running any of the examples you need to have a Recorded Future API token to be passed to PSEngine. This can be done in few ways:

1. set a `RF_TOKEN` environment variable. For example on Linux or MacOS you will do:

    ```bash
    export RF_TOKEN=<your_token>
    ```

2. Load the environment variable from a `.env` file using the `python-dotenv` module <https://pypi.org/project/python-dotenv/>

3. Get the token from a vault and pass it as argument to each manager. For example:

    ```python
    from psengine.enrich import LookupMgr

    token = ... # steps to collect the token
    mgr = LookupMgr(rf_token=token)

    ```


The [Internals](internals.md) page is going to go deeper in some of the internal code of PSEngine in case you need to read through it during troubleshooting/debugging.

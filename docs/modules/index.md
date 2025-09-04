In this section, we present how to use each module with easy-to-follow examples.

Note that some examples might not be 100% reproducible since they rely on your Recorded Future enterprise being correctly set up, having the right modules, and the correct permissions on the token, etc. Those examples are marked with a tip box, with possible steps you might need to take to complete the example.

Also, before running any of the examples, you need a Recorded Future API token to pass to PSEngine. You can do this in a few ways:

- Set an `RF_TOKEN` environment variable. For example, on Linux or macOS you would run:

    ```bash
    export RF_TOKEN=<your_token>
    ```

- Load the environment variable from a `.env` file using the `python-dotenv` module <https://pypi.org/project/python-dotenv/>.

- Get the token from a vault and pass it as an argument to each manager. For example:

    ```python
    from psengine.enrich import LookupMgr

    token = ...  # steps to collect the token
    mgr = LookupMgr(rf_token=token)
    ```

The [Internals](../internals.md) page goes deeper into some of the internal code of PSEngine in case you need to read through it during troubleshooting/debugging.

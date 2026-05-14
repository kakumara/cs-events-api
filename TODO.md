This api could be improved further by

1. Swap the in memory events store and search with a Database backed store and serach. Ideally with seperate schema per tenant
2. Extending to include a proper authentication and authorization framework. Currently the tenant identifer is passed as a header variable for simplicity which is not ideal. Could use the auth context to retrive the tenant id.
3. A shared logging configuration across codebase/modules.
4. Better error handling. For example overriding fastapi validation errors custom exception handlers

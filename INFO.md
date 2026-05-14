### Key decisions and trade-offs
1. Adopting an in memory store for events for simplicity. (dictionary based)
2. Using FastAPI + uv as the API server/framework. This allowed faster and simpler implementation.
3. Using a header variable to pass the tenant id. Once again for simplicity.
4. Preffered `apscheduler` (over `fastapi_utils.tasks`) which seems to be a more popular approach.  

### Further improvemnt points

1. Swap the in memory events store and search with a Database backed store and serach. Ideally with seperate schema per tenant
2. Extending to include a proper authentication and authorization framework. Currently the tenant identifer is passed as a header variable for simplicity which is not ideal. Could use the auth context to retrive the tenant id.
3. A shared logging configuration across codebase/modules.
4. Better error handling. For example overriding fastapi validation errors custom exception handlers

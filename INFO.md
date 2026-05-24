### Key decisions and trade-offs
1. Adopting an in memory store for events for simplicity. (dictionary based). Tenant isolation is handled using separate dictionaries per tenant.
2. For each tenant, events are stored as a sub dictionary with `event_id` being the key. This allows to avoid duplicate events for the tenant.
3. Using FastAPI + uv as the API server/framework. This allowed faster and simpler implementation.
4. Using a header variable to pass the tenant id. Once again for simplicity.
5. Preffered `apscheduler` (over `fastapi_utils.tasks`) which seems to be a more popular approach.  

### Further improvemnt points

1. Swap the in memory events store and search with a Database backed store and serach. Ideally with seperate schema per tenant (ability to index based on query criteria and provides scalabilty)
2. Extending to include a proper authentication and authorization framework. Currently the tenant identifer is passed as a header variable for simplicity which is not ideal. Could use the auth context to retrive the tenant id.
3. A shared logging configuration across codebase/modules.
4. Better error handling. For example overriding fastapi validation errors custom exception handlers
5. add pagination support for query api. (scalability for large datasets)
6. Auto-data loading mechanism form a speicifc disk location. (monitor and ingest new files). This can be a separate job/process that to the query API.
7. Data retention/cleanup job to be a separate process (or can even be a policy in database)

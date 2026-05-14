# CS Events API

### Requirements:
 - Python >= 3.13
 - [uv](https://github.com/astral-sh/uv) 

### Cloning and Running 
- clone the repository
- run `uv sync` -- (from project directory) to install the dependencies
- run `uv run fastapi run` -- (from project directory) to start the server
- To test use any rest client. here is an example `curl` request (assumes json_pp is installed)
```
curl -H "X-Tenant-ID: acme_corp" http://localhost:8000/events | json_pp
```
- More examples can be found in [example.http](./example.http) file. (this can be directly used by vscode [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) extension)
- You can also view/test the API via the fastAPI docs swagger UI 
```
http://localhost:8000/docs
```

### Running tests
- run `uv run pytest` (from project directory)
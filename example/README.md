To run this example:

1. Start a running Postgres instance. You can do this locally on your machine, or via docker, or using a cloud provider e.g. AWS's RDS

2. Setup the schema `psql -f setup.psql --set API_PASSWORD=changeme`

3. Start PostgREST (use postgrest.config as a template)

4. Run the python entrypoint: `python main.py`


## Example Output

```
$ python example/main.py
All foos:
   []
All foos (after insert):
   [{'id': '0d658c52-875a-11e9-8088-bf81b5512b44', 'name': 'my foo', 'created_at': '2019-06-05T16:20:45.307079+10:00'}]
Contains 'different':
   {'id': '0d65f9d0-875a-11e9-8088-03add6e63500', 'name': 'a different name', 'created_at': '2019-06-05T16:20:45.31001+10:00'}
Before 2010:
   []
All foos (after delete):
   []
```

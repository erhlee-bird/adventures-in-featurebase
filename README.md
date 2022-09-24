# adventures-in-featurebase

I've long wanted to do some exploration of Pilosa then Molecula now FeatureBase
and I've finally sat down to do so.

I'm working with a free trial of the cloud offering and setting up some tables
and ingest endpoints.

This repo contains various notes and utilities from my investigations.

- https://cloud.featurebase.com/
- https://docs.featurebase.com/
- https://api-docs-featurebase-cloud.redoc.ly/

## Log

### Setting Up

Created a clean database. Talking with the team, it seems like a common pattern
is to maybe have a staging and prod database but you are initially limited to
just one during the trial.

Created a table. You add columns/fields after creating the table. The only
decision you have to make up front is whether or not to have your ID type be a
Number or a String. I believe the intuition is that if you have rows that you
don't really need coalesced and merged and just want to continue aggregating
rows, Numbers are pretty suitable. In my case, I'm storing data about files and
want to uniquely identify them by a content hash (SHA256) so I chose to use a
String type.

> **_NOTE:_** This is where I encountered my first major confusion with the API
>             docs at the time. If you choose to programmatically create a table,
>             you must set an undocumented field (`trackExistence`) to true.
>             When I created a table without it set, I was unable to make any
>             queries against the table without errors.

```shell
# Status code will be 201 for successful creation.

curl \
  -d "{\"name\": \"${TABLE_NAME}\", \"options\": {\"keys\": true, \"trackExistence\": true}}" \
  -H "Authorization: Bearer ${FEATUREBASE_TOKEN}" \
  -Ls \
  -o /dev/null \
  -w "%{http_code}" \
  "https://api.featurebase.com/v2/tables/${DATABASE_ID}")"
```

### Adding Columns

One of the immediate challenges posed was using the API to add fields to a
table.

> Creating a column can also be accomplished programmatically, but is not 
> recommended at this time.

:see_no_evil: :hear_no_evil:

You can do this via the UI, but, as I am in the process of learning the data
model and making rapid changes, I prefer to have an reliable programmatic
interface to work with.

Figuring out what types were available was **really** challenging.
From the UI, I could glean that there were the following column types:

- int
- timestamp
- decimal
- string
- stringset
- id
- idset

Looking at the [documentation](https://docs.featurebase.com/reference/api/enterprise/http-api#create-field),
there are only a handful of analogs to the types presented in the UI.

- set
- int
- timestamp
- bool
- time
- mutex

This was immediately pretty confusing. To get an accurate mapping to reconcile
the different types, I put together a [Selenium script](scripts/python/discover_field_payloads.py)
to add columns in the web UI and observe the payloads passed to the API from
the frontend.

This turned out to be very worthwhile and I observed the following
(see [data/field_payloads.jsonl](data/field_payloads.jsonl)):

```json
int,{"options":{"type":"int","min":-9007199254740991,"max":9007199254740991}}
timestamp,{"options":{"type":"timestamp","timeUnit":"s"}}
decimal,{"options":{"type":"decimal","scale":2}}
string,{"options":{"type":"mutex","keys":true}}
stringset,{"options":{"type":"set","keys":true}}
id,{"options":{"type":"mutex"}}
idset,{"options":{"type":"set"}}
```

> **_NOTE_:** Curious that the `int` type has a 53-bit range by default.
>             The documentation that says it can go up to 63-bits of storage.

Using these options as an oracle, I was able to go ahead and create some tables
with some more confidence.

### Adding a Sink

For the cloud offering, users are meant to add Data Sources. Creating one
creates a "persistent ingest endpoint that allows you to push data into your
database over HTTPS."

In the UI, you specify a "Source name", "Database", "Target table",
"Column mappings", and a setting to either allow or reject incoming records
that have missing values.

I walked through this exercise for the table I created and instrumented to
generate the `data/field_payloads.jsonl` file above and wrote the API payload to
[data/create_sink.json](data/create_sink.json).

```json
    "schema": {
        "type": "json",
        "id_field": null,
        "primary_key_fields": [
            "_id"
        ],
        "allow_missing_fields": true,
        "definition": [
            {
                "name": "_id",
                "path": [
                    "d"
                ],
                "type": "string"
            },
            {
                "name": "a",
                "path": [
                    "a"
                ],
                "type": "int",
                "config": {
                    "Min": -9007199254740991,
                    "Max": 9007199254740991,
                    "ForeignIndex": ""
                }
            },
            {
                "name": "b",
                "path": [
                    "b"
                ],
                "type": "timestamp",
                "config": {
                    "Granularity": "s"
                }
            },
            {
                "name": "c",
                "path": [
                    "c"
                ],
                "type": "decimal",
                "config": {
                    "Scale": 2
                }
            },
            {
                "name": "d",
                "path": [
                    "d"
                ],
                "type": "string",
                "config": {
                    "Mutex": true
                }
            },
            {
                "name": "e",
                "path": [
                    "e"
                ],
                "type": "string",
                "config": {
                    "Mutex": false
                }
            },
            {
                "name": "f",
                "path": [
                    "f"
                ],
                "type": "id",
                "config": {
                    "Mutex": true
                }
            },
            {
                "name": "g",
                "path": [
                    "g"
                ],
                "type": "id",
                "config": {
                    "Mutex": false
                }
            }
        ]
    }
```

This was a bit disheartening as there was a whole new discrepant type notation to
navigate.

So creating a `string` column in the UI sends a `mutex` type through the API
which gets configured in the sink as a `string` type with a `Mutex` config.

Musing, it seems like there could be some more consistency and clarity in how
these types and options are mapped through this sequence. Additionally, it seems
redundant to have to pass in type configuration for the sink creation API. Having
specified a target table and field name, wouldn't it be safer to just let
FeatureBase look up and provide the type of the field?

## Development

TODO: Set up a Nix Devcontainer.

```
export NIXPKGS_ALLOW_UNFREE=1

nix-shell
```

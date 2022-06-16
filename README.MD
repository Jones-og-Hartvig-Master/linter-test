# Linter test
Repository for tests of the CodeQL queries at [energy-queries](https://github.com/Jones-og-Hartvig-Master/energy-queries).

## Usage

Args:

- `-a`, `--analyze` - analyze the list of repositories in `input.json` for code smells
- `-m`, `--manual-check` - analyze the set of repositores categorized as in need for a manual check
- `-c`, `--cleanup` - move all the results to the results directory and remove repositories (see [Manual Check](#manual-check))

---

First populate `input.json` with a list of GitHub repository links, e.g.,

```json
{
    "repos": [
        "https://github.com/Jones-og-Hartvig-Master/energy-queries",
        "https://github.com/Jones-og-Hartvig-Master/CodeSmells",
        ...
    ]
}
```

then run the following command

```shell
python fetch.py -a -c
```

To re-run the repositories in need of a manual check, run the following command

```shell
python fetch.py -m -c
```

## Results
Results are stored in a directory on the format `DDMMYYY`

### CSV
CSV files containing the CodeQL results for a given repository. 
These are located in the results dir `DDMMYYYY/codeql`.

Each CSV file has the name of the repository, refer to `approved.json` for more information.

### Approved
Stored in `DDMMYYYY/approved.json`.

Repositories marked `approved` have confirmed results of code smells.

### Denied
Stored in `DDMMYYYY/denied.json`.

Repositories marked `denied` have no code smells.

### Manual check
Stored in `manual_check.json`.

Repositories marked `manual_check` were unable to be processed, most likely because of a faulty location when running the CodeQL script.
In most cases this can be alleviated by modifying `codeql.sh` located in that specific repository directory.

This can be done by changing directory to a proper location where the CodeQL database can be generated, and moving the results file to the root directory, e.g.,
**Note that the CodeQL file modified must be the one located in the repository directory.**

```shell
#!/bin/bash

DB_NAME="smelldb"
LANG="csharp"

cd src/SomeDir # added: change to proper location

echo "################# cleaning up"
rm -r $DB_NAME
echo "################# creating database for project"
codeql database create $DB_NAME --language=$LANG
echo "################# analysing database"
codeql database analyze $DB_NAME --format=csv --output=res.csv csharp-energy-aware-queries
echo "Done. Results written to res.csv"

mv res.csv ../../ # added: move the results file to root
```
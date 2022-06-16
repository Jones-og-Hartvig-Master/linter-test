#!/bin/bash

DB_NAME="smelldb"
LANG="csharp"

echo "################# cleaning up"
rm -r $DB_NAME
echo "################# creating database for project"
codeql database create $DB_NAME --language=$LANG
echo "################# analysing database"
codeql database analyze $DB_NAME --format=csv --output=res.csv csharp-energy-aware-queries
echo "Done. Results written to res.csv"
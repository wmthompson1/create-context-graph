param(
    [ValidateSet("validate", "query", "endpoint")]
    [string]$Command = "validate",
    [string]$Query = "salt-manufacturing.sparql",
    [int]$Port = 8080
)

$ErrorActionPreference = "Stop"
$ontologyRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repositoryRoot = Resolve-Path (Join-Path $ontologyRoot "..\..\..\..\..")
$relativeOntologyRoot = "my-mrp-kb/ontology/salt/manufacturing/v1.0"
$containerOntologyRoot = "/workspace/$relativeOntologyRoot"
$image = "ontop/ontop:5.3.0"
$baseArgs = @(
    "run", "--rm",
    "-v", "${repositoryRoot}:/workspace",
    "-v", "${repositoryRoot}/$relativeOntologyRoot/drivers:/opt/ontop/jdbc:ro",
    $image, "ontop", $Command,
    "-m", "$containerOntologyRoot/salt-manufacturing.obda",
    "-p", "$containerOntologyRoot/ontop.properties",
    "-t", "$containerOntologyRoot/salt-manufacturing.ttl"
)

switch ($Command) {
    "validate" { & docker @baseArgs }
    "query" { & docker @baseArgs "-q" "$containerOntologyRoot/$Query" }
    "endpoint" { & docker run --rm -p "${Port}:8080" -v "${repositoryRoot}:/workspace" -v "${repositoryRoot}/$relativeOntologyRoot/drivers:/opt/ontop/jdbc:ro" $image ontop endpoint -m "$containerOntologyRoot/salt-manufacturing.obda" -p "$containerOntologyRoot/ontop.properties" -t "$containerOntologyRoot/salt-manufacturing.ttl" --port 8080 }
}
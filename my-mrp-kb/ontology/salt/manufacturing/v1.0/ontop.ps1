param(
    [ValidateSet("validate", "query", "endpoint")]
    [string]$Command = "validate",
    [string]$Query = "salt-manufacturing.sparql",
    [int]$Port = 8080,
    [string]$OntologyRoot = (Split-Path -Parent $MyInvocation.MyCommand.Path)
)

$ErrorActionPreference = "Stop"
$ontologyRoot = Resolve-Path $OntologyRoot
$driverRoot = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "drivers"
if (-not (Test-Path $driverRoot)) {
    throw "Ontop JDBC driver directory does not exist: $driverRoot"
}
$containerOntologyRoot = "/ontology"
$image = "ontop/ontop:5.3.0"
$baseArgs = @(
    "run", "--rm",
    "-v", "${ontologyRoot}:/ontology:ro",
    "-v", "${driverRoot}:/opt/ontop/jdbc:ro",
    $image, "ontop", $Command,
    "-m", "$containerOntologyRoot/salt-manufacturing.obda",
    "-p", "$containerOntologyRoot/ontop.properties",
    "-t", "$containerOntologyRoot/salt-manufacturing.ttl"
)

switch ($Command) {
    "validate" { & docker @baseArgs }
    "query" { & docker @baseArgs "-q" "$containerOntologyRoot/$Query" }
    "endpoint" { & docker run --rm -p "${Port}:8080" -v "${ontologyRoot}:/ontology:ro" -v "${driverRoot}:/opt/ontop/jdbc:ro" $image ontop endpoint -m "$containerOntologyRoot/salt-manufacturing.obda" -p "$containerOntologyRoot/ontop.properties" -t "$containerOntologyRoot/salt-manufacturing.ttl" --port 8080 }
}

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
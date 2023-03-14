# Sonarqube Semgrep

## Goal

Use sonarqube to review findings from semgrep

## Setup

### start server

(if you don't already have one running)

```
docker compose up -d
```

This will get sonarqube server running on http://localhost:9000

##### first server run

If container is freshly created, reset admin password and generate an integration token, for the scanner

### scan code with semgrep

Run your semgrep rules in the code and generate a JSON report

```
$ semgrep --json -o semgrep.json \
          -f ~/my-rules/ \
          /path/to/code/base/
```

### scan code with sonar-scanner

Download [sonar-scanner](https://docs.sonarqube.org/9.9/analyzing-source-code/scanners/sonarscanner/).

Re-scan the code with sonar-scanner to upload codebase and external issues.

[scan.py](scan.py) wraps that:

```
$ ./scan.py sqp_TOKEN_GENERATED_IN_THE_UI \
            /path/to/code/base/ \
            ./semgrep.json
```

If using external sonarqube

```
$ ./scan.py --sonar-host https://sonarqube.my.internal/ \
            --sonar-project TEST_SomeUniqueProjectName \
            sqp_TOKEN_GENERATED_IN_THE_UI \
            /path/to/code/base/ \
            ./semgrep.json
```

Full usage:

```
./scan.py -h
usage: scan.py [-h] [--scanner-bin SCANNER_BIN] [--sonar-host SONAR_HOST] [--sonar-project SONAR_PROJECT] api-key source report

positional arguments:
  api-key               API key to upload analysis
  source                Path to sources to scan
  report                Path to semgrep report (JSON format)
  extra                 Any extra arguments to pass to sonar-scanner (ie: -Dsonar.exclusions=XX)

options:
  -h, --help            show this help message and exit
  --scanner-bin SCANNER_BIN
                        Path to sonar-scanner binary (if not in $PATH) (default: sonar-scanner)
  --sonar-host SONAR_HOST
                        Sonar server URL (default: http://localhost:9000)
  --sonar-project SONAR_PROJECT
                        Sonar project key (default: testing)
```

Extra options to `sonar-scanner` can be set in `sonar-project.properties` in the root of the project or passed via the `extra` arguments

```
$ ./scan.py sqp_TOKEN_GENERATED_IN_THE_UI \
            /path/to/code/base/ \
            ./semgrep.json
            -- -Dsonar.exclusions='tests/**/*'
```

# Airflow DAGs

Orchestration DAGs for the DataOps platform. Each DAG uses the `dataops`
package for lineage tracking and data-quality gating.

## DAGs

| DAG                    | Schedule  | Purpose                                             |
| ---------------------- | --------- | --------------------------------------------------- |
| `etl_pipeline`         | `@daily`  | Extract -> transform -> load the events dataset.    |
| `data_quality_checks`  | `@hourly` | Run quality expectations across curated datasets.   |

## Local usage

Point Airflow at this folder as its DAGs directory and ensure the `dataops`
package is installed in the same environment:

```bash
pip install -e ".[dev]"
export AIRFLOW__CORE__DAGS_FOLDER="$(pwd)/airflow/dags"
airflow dags list
```

The DAGs import from `dataops` (`DataOpsService`, `QualityRule`, `Dataset`), so
the package must be importable by the Airflow workers.

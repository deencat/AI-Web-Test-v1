# AI Web Test v1.0 - MLOps Architecture
## Comprehensive Model Lifecycle Management

**Version:** 1.0  
**Date:** October 27, 2025  
**Priority:** P0 - Critical  
**Status:** Production-Ready Architecture  

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [MLOps Maturity Model](#mlops-maturity-model)
3. [Complete MLOps Stack](#complete-mlops-stack)
4. [Experiment Tracking](#experiment-tracking)
5. [Model Registry & Versioning](#model-registry--versioning)
6. [Feature Store](#feature-store)
7. [Data Versioning](#data-versioning)
8. [A/B Testing Framework](#ab-testing-framework)
9. [Drift Detection & Monitoring](#drift-detection--monitoring)
10. [Automated Retraining Pipeline](#automated-retraining-pipeline)
11. [Model Governance](#model-governance)
12. [CI/CD for ML](#cicd-for-ml)
13. [Implementation Roadmap](#implementation-roadmap)

---

## Executive Summary

This document addresses the **MLOps maturity gap** identified in the AI Web Test v1.0 documentation. It provides a comprehensive, production-ready MLOps architecture following industry best practices for 2025.

**What's Covered:**
- ✅ Complete MLOps stack with specific tools
- ✅ MLflow experiment tracking and model registry
- ✅ Detailed A/B testing implementation
- ✅ Drift detection with concrete thresholds
- ✅ Automated retraining pipeline architecture
- ✅ Model governance and approval workflows
- ✅ Feature store for consistency
- ✅ Data versioning strategy

**Implementation Timeline:** 15 days (integrated into Phases 2-3)

---

## MLOps Maturity Model

### Current State: Level 1 → Target State: Level 3

```
Level 0: Manual Process
  ❌ Manual model training
  ❌ No version control
  ❌ Manual deployment

Level 1: DevOps but no MLOps (CURRENT - Partially)
  ✅ Scripts for training
  ✅ Git for code versioning
  ⚠️ Limited experiment tracking
  ❌ Manual model deployment

Level 2: Automated Training (TARGET - Phase 2)
  ✅ MLflow experiment tracking
  ✅ Model registry
  ✅ Automated CI/CD pipeline
  ✅ Monitoring dashboards
  ⚠️ Manual retraining decisions

Level 3: Automated Deployment (TARGET - Phase 3)
  ✅ Automated A/B testing
  ✅ Automated drift detection
  ✅ Automated retraining triggers
  ✅ Model governance workflows
  ✅ Feature store integration

Level 4: Full MLOps Automation (FUTURE - Phase 4)
  ✅ AutoML for hyperparameter tuning
  ✅ Automated feature engineering
  ✅ Self-healing pipelines
  ✅ Multi-model orchestration
```

**Our Goal:** Reach Level 3 by end of Phase 3 (Week 24)

---

## Complete MLOps Stack

### Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     MLOPS PLATFORM STACK                         │
└──────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ EXPERIMENTATION & TRAINING                                      │
├─────────────────────────────────────────────────────────────────┤
│ MLflow                    | Experiment tracking, model registry │
│ Weights & Biases (W&B)    | Alternative/complementary tracking  │
│ TensorBoard               | Training visualization              │
│ Optuna                    | Hyperparameter optimization         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ DATA & FEATURE MANAGEMENT                                       │
├─────────────────────────────────────────────────────────────────┤
│ Feast                     | Feature store (online + offline)    │
│ DVC (Data Version Control)| Version datasets & large files      │
│ Great Expectations        | Data validation & quality checks    │
│ PostgreSQL                | Feature metadata storage            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ MODEL SERVING & DEPLOYMENT                                      │
├─────────────────────────────────────────────────────────────────┤
│ BentoML                   | Model serving framework             │
│ FastAPI                   | REST API endpoints                  │
│ ONNX Runtime              | Model optimization & inference      │
│ TensorRT                  | GPU inference acceleration          │
│ Nginx/Envoy               | Load balancing & traffic splitting  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ MONITORING & OBSERVABILITY                                      │
├─────────────────────────────────────────────────────────────────┤
│ Prometheus                | Metrics collection                  │
│ Grafana                   | Visualization & dashboards          │
│ Evidently AI              | ML-specific monitoring & drift      │
│ WhyLogs                   | Data logging & profiling            │
│ Sentry                    | Error tracking                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ ORCHESTRATION & AUTOMATION                                      │
├─────────────────────────────────────────────────────────────────┤
│ Airflow                   | Workflow orchestration              │
│ Prefect                   | Alternative to Airflow              │
│ GitHub Actions            | CI/CD automation                    │
│ ArgoCD                    | GitOps for Kubernetes               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ GOVERNANCE & COMPLIANCE                                         │
├─────────────────────────────────────────────────────────────────┤
│ MLflow Model Registry     | Model approval workflows            │
│ Git                       | Code & config version control       │
│ Audit Logs                | Track all model changes             │
│ Model Cards               | Documentation & metadata            │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Selection Matrix

| Component | Primary Choice | Alternative | Reason |
|-----------|---------------|-------------|--------|
| **Experiment Tracking** | MLflow | W&B | Open source, self-hosted, mature |
| **Model Registry** | MLflow Registry | Custom | Integrated with tracking |
| **Feature Store** | Feast | Tecton | Open source, CNCF project |
| **Data Versioning** | DVC | Git LFS | Handles large datasets |
| **Model Serving** | BentoML | TorchServe | Easy deployment, multi-framework |
| **Orchestration** | Airflow | Prefect | Industry standard, mature |
| **Monitoring** | Evidently AI | WhyLabs | Open source, ML-specific |
| **Drift Detection** | Evidently AI | Alibi Detect | Built-in metrics |

---

## Experiment Tracking

### MLflow Setup

**Architecture:**

```
┌──────────────────────────────────────────────────────────────┐
│                   MLFLOW ARCHITECTURE                         │
└──────────────────────────────────────────────────────────────┘

Training Scripts (Python)
        ↓
   MLflow Client
        ↓
┌─────────────────┐
│ MLflow Tracking │ ← Log params, metrics, artifacts
│     Server      │
└────────┬────────┘
         ↓
┌────────────────────────────────────────────┐
│ Backend Store (PostgreSQL)                 │
│ - Experiments                              │
│ - Runs                                     │
│ - Parameters                               │
│ - Metrics                                  │
│ - Tags                                     │
└────────────────────────────────────────────┘
         ↓
┌────────────────────────────────────────────┐
│ Artifact Store (MinIO / S3)                │
│ - Model files (.pt, .onnx)                 │
│ - Plots & visualizations                   │
│ - Training logs                            │
│ - Confusion matrices                       │
└────────────────────────────────────────────┘
```

**Installation & Configuration:**

```bash
# Install MLflow
pip install mlflow==2.9.2 psycopg2-binary boto3

# Set up MLflow tracking server
mlflow server \
  --backend-store-uri postgresql://user:pass@localhost:5432/mlflow \
  --default-artifact-root s3://mlflow-artifacts \
  --host 0.0.0.0 \
  --port 5000

# Or using Docker Compose
```

**docker-compose.mlflow.yml:**

```yaml
version: '3.8'

services:
  mlflow-db:
    image: postgres:15
    environment:
      POSTGRES_DB: mlflow
      POSTGRES_USER: mlflow
      POSTGRES_PASSWORD: mlflow_password
    volumes:
      - mlflow-db-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  mlflow-minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - mlflow-minio-data:/data
    ports:
      - "9000:9000"
      - "9001:9001"

  mlflow-server:
    image: ghcr.io/mlflow/mlflow:v2.9.2
    depends_on:
      - mlflow-db
      - mlflow-minio
    environment:
      MLFLOW_S3_ENDPOINT_URL: http://mlflow-minio:9000
      AWS_ACCESS_KEY_ID: minioadmin
      AWS_SECRET_ACCESS_KEY: minioadmin
    command: >
      mlflow server
      --backend-store-uri postgresql://mlflow:mlflow_password@mlflow-db:5432/mlflow
      --default-artifact-root s3://mlflow-artifacts
      --host 0.0.0.0
      --port 5000
    ports:
      - "5000:5000"

volumes:
  mlflow-db-data:
  mlflow-minio-data:
```

**Usage in Training Code:**

```python
# train_with_mlflow.py
import mlflow
import mlflow.pytorch
from mlflow.models import infer_signature

# Set MLflow tracking URI
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("aiwebtest-generation-agent")

# Start MLflow run
with mlflow.start_run(run_name="dqn-v1-exp001"):
    
    # Log hyperparameters
    mlflow.log_params({
        "learning_rate": 0.0003,
        "batch_size": 256,
        "gamma": 0.99,
        "epsilon_start": 1.0,
        "epsilon_decay": 0.995,
        "epsilon_min": 0.01,
        "buffer_size": 1000000,
        "network_architecture": "dueling-dqn",
        "gpu_count": 3,
        "agent_type": "generation_agent"
    })
    
    # Training loop
    for episode in range(num_episodes):
        # ... training code ...
        
        # Log metrics every episode
        mlflow.log_metrics({
            "episode_reward": episode_reward,
            "episode_length": episode_length,
            "loss": loss,
            "epsilon": epsilon,
            "q_value_mean": q_value_mean,
            "learning_rate": current_lr
        }, step=episode)
        
        # Log additional metrics every 100 episodes
        if episode % 100 == 0:
            mlflow.log_metrics({
                "avg_reward_100": np.mean(rewards[-100:]),
                "success_rate": success_rate,
                "exploration_rate": epsilon
            }, step=episode)
    
    # Log model
    mlflow.pytorch.log_model(
        pytorch_model=model,
        artifact_path="model",
        registered_model_name="generation-agent-dqn",
        signature=infer_signature(sample_input, sample_output)
    )
    
    # Log artifacts
    mlflow.log_artifact("training_curves.png")
    mlflow.log_artifact("confusion_matrix.png")
    mlflow.log_artifact("config.yaml")
    
    # Log final metrics
    mlflow.log_metrics({
        "final_avg_reward": final_avg_reward,
        "training_time_seconds": training_time,
        "total_episodes": num_episodes
    })
    
    # Set tags for filtering
    mlflow.set_tags({
        "model_type": "DQN",
        "agent": "generation_agent",
        "gpu_type": "RTX3070",
        "framework": "pytorch",
        "stage": "development"
    })
```

**Viewing Experiments:**

```bash
# Access MLflow UI
# Open http://localhost:5000 in browser

# Or use MLflow API
import mlflow

# List all experiments
experiments = mlflow.search_experiments()

# Search runs
runs = mlflow.search_runs(
    experiment_names=["aiwebtest-generation-agent"],
    filter_string="metrics.avg_reward_100 > 80",
    order_by=["metrics.avg_reward_100 DESC"]
)

# Get best run
best_run = runs.iloc[0]
print(f"Best run: {best_run['run_id']}")
print(f"Best reward: {best_run['metrics.avg_reward_100']}")
```

---

## Model Registry & Versioning

### MLflow Model Registry

**Model Lifecycle States:**

```
┌─────────────────────────────────────────────────────────────┐
│            MODEL LIFECYCLE IN REGISTRY                      │
└─────────────────────────────────────────────────────────────┘

None (Initial)
    ↓ [Register Model]
Staging
    ↓ [Validation Passed & Approve]
Production
    ↓ [New Model Deployed]
Archived
    ↓ [Cleanup Old Models]
Deleted
```

**Model Registration:**

```python
# register_model.py
import mlflow
from mlflow.tracking import MlflowClient

mlflow.set_tracking_uri("http://localhost:5000")
client = MlflowClient()

def register_model(run_id, model_name, description=""):
    """Register model from MLflow run."""
    
    # Register model
    model_uri = f"runs:/{run_id}/model"
    model_version = mlflow.register_model(
        model_uri=model_uri,
        name=model_name,
        tags={
            "framework": "pytorch",
            "agent_type": "generation_agent"
        }
    )
    
    # Update model version description
    client.update_model_version(
        name=model_name,
        version=model_version.version,
        description=description
    )
    
    # Add metadata
    client.set_model_version_tag(
        name=model_name,
        version=model_version.version,
        key="validation_status",
        value="pending"
    )
    
    return model_version

def promote_to_staging(model_name, version):
    """Promote model version to Staging."""
    
    client.transition_model_version_stage(
        name=model_name,
        version=version,
        stage="Staging",
        archive_existing_versions=False
    )
    
    print(f"Model {model_name} v{version} promoted to Staging")

def promote_to_production(model_name, version):
    """Promote model version to Production."""
    
    # Archive existing production models
    client.transition_model_version_stage(
        name=model_name,
        version=version,
        stage="Production",
        archive_existing_versions=True  # Archive old production
    )
    
    # Add production timestamp
    client.set_model_version_tag(
        name=model_name,
        version=version,
        key="production_deployment_date",
        value=datetime.now().isoformat()
    )
    
    print(f"Model {model_name} v{version} promoted to Production")

def rollback_model(model_name, to_version):
    """Rollback to previous model version."""
    
    # Demote current production
    current_prod = client.get_latest_versions(model_name, stages=["Production"])[0]
    client.transition_model_version_stage(
        name=model_name,
        version=current_prod.version,
        stage="Archived"
    )
    
    # Promote target version to production
    promote_to_production(model_name, to_version)
    
    print(f"Rolled back {model_name} to version {to_version}")
```

**Model Versioning Strategy:**

```python
# model_versioning.py

class ModelVersionManager:
    """
    Manages model versions with semantic versioning.
    
    Version format: MAJOR.MINOR.PATCH
    - MAJOR: Breaking changes (new architecture)
    - MINOR: New features (improved training)
    - PATCH: Bug fixes (minor tweaks)
    """
    
    def __init__(self, model_name):
        self.model_name = model_name
        self.client = MlflowClient()
    
    def get_latest_version(self, stage="Production"):
        """Get latest model version in stage."""
        versions = self.client.get_latest_versions(
            self.model_name,
            stages=[stage]
        )
        if versions:
            return versions[0].version
        return None
    
    def create_version(self, run_id, version_type="patch"):
        """
        Create new model version with semantic versioning.
        
        Args:
            run_id: MLflow run ID
            version_type: 'major', 'minor', or 'patch'
        """
        # Get current version
        current_version = self.get_latest_version()
        
        if current_version:
            major, minor, patch = map(int, current_version.split('.'))
            
            if version_type == "major":
                new_version = f"{major+1}.0.0"
            elif version_type == "minor":
                new_version = f"{major}.{minor+1}.0"
            else:  # patch
                new_version = f"{major}.{minor}.{patch+1}"
        else:
            new_version = "1.0.0"
        
        # Register model
        model_version = register_model(
            run_id=run_id,
            model_name=self.model_name,
            description=f"Version {new_version}"
        )
        
        # Tag with semantic version
        self.client.set_model_version_tag(
            name=self.model_name,
            version=model_version.version,
            key="semantic_version",
            value=new_version
        )
        
        return model_version, new_version
```

**Loading Models:**

```python
# load_model.py
import mlflow

def load_production_model(model_name):
    """Load current production model."""
    model_uri = f"models:/{model_name}/Production"
    model = mlflow.pytorch.load_model(model_uri)
    return model

def load_specific_version(model_name, version):
    """Load specific model version."""
    model_uri = f"models:/{model_name}/{version}"
    model = mlflow.pytorch.load_model(model_uri)
    return model

def compare_models(model_name, version1, version2, test_data):
    """Compare two model versions."""
    model1 = load_specific_version(model_name, version1)
    model2 = load_specific_version(model_name, version2)
    
    # Evaluate both models
    metrics1 = evaluate_model(model1, test_data)
    metrics2 = evaluate_model(model2, test_data)
    
    return {
        f"v{version1}": metrics1,
        f"v{version2}": metrics2,
        "improvement": {
            k: metrics2[k] - metrics1[k]
            for k in metrics1.keys()
        }
    }
```

---

## Feature Store

### Feast Setup

**Why Feature Store:**
- ✅ Consistent features between training and serving
- ✅ Feature reusability across models
- ✅ Point-in-time correctness for training
- ✅ Low-latency feature serving

**Architecture:**

```
┌──────────────────────────────────────────────────────────────┐
│                  FEAST ARCHITECTURE                           │
└──────────────────────────────────────────────────────────────┘

Offline Store (PostgreSQL)           Online Store (Redis)
├─ Historical features               ├─ Real-time features
├─ Training data generation          ├─ Low-latency serving (<10ms)
└─ Point-in-time joins               └─ Latest feature values

        ↓                                     ↓
    Training                              Inference
    Pipeline                              Pipeline
```

**Installation:**

```bash
pip install feast==0.35.0 feast[redis,postgres]
```

**Feature Repository Setup:**

```python
# feature_repo/feature_store.yaml
project: aiwebtest
registry: s3://feast-registry/registry.db
provider: local
online_store:
  type: redis
  connection_string: "localhost:6379"
offline_store:
  type: postgres
  host: localhost
  port: 5432
  database: feast
  user: feast
  password: feast_password
```

**Feature Definitions:**

```python
# feature_repo/features.py
from feast import Entity, Feature, FeatureView, Field, ValueType
from feast.types import Float32, Int64, String
from datetime import timedelta

# Define entities
test_entity = Entity(
    name="test_id",
    value_type=ValueType.STRING,
    description="Test case identifier"
)

agent_entity = Entity(
    name="agent_id",
    value_type=ValueType.STRING,
    description="Agent identifier"
)

# Define feature view for test execution features
test_execution_features = FeatureView(
    name="test_execution_features",
    entities=[test_entity],
    ttl=timedelta(days=30),
    schema=[
        Field(name="execution_time_ms", dtype=Float32),
        Field(name="pass_rate_7d", dtype=Float32),
        Field(name="pass_rate_30d", dtype=Float32),
        Field(name="failure_count", dtype=Int64),
        Field(name="last_execution_status", dtype=String),
        Field(name="avg_retry_count", dtype=Float32),
        Field(name="flakiness_score", dtype=Float32),
    ],
    online=True,
    source=BatchSource(
        timestamp_field="event_timestamp",
        created_timestamp_column="created_timestamp",
        path="s3://feast-data/test_executions.parquet"
    ),
    tags={"team": "qa", "domain": "test_automation"}
)

# Define feature view for agent context
agent_context_features = FeatureView(
    name="agent_context_features",
    entities=[agent_entity],
    ttl=timedelta(days=7),
    schema=[
        Field(name="recent_accuracy", dtype=Float32),
        Field(name="recent_reward", dtype=Float32),
        Field(name="tests_generated_24h", dtype=Int64),
        Field(name="success_rate_7d", dtype=Float32),
        Field(name="avg_confidence_score", dtype=Float32),
    ],
    online=True,
    source=BatchSource(
        timestamp_field="event_timestamp",
        path="s3://feast-data/agent_metrics.parquet"
    )
)
```

**Using Features in Training:**

```python
# training_with_features.py
from feast import FeatureStore
import pandas as pd

# Initialize feature store
store = FeatureStore(repo_path="feature_repo/")

# Get historical features for training
entity_df = pd.DataFrame({
    "test_id": ["test_001", "test_002", "test_003"],
    "event_timestamp": pd.to_datetime([
        "2025-10-01", "2025-10-02", "2025-10-03"
    ])
})

# Retrieve features
training_df = store.get_historical_features(
    entity_df=entity_df,
    features=[
        "test_execution_features:execution_time_ms",
        "test_execution_features:pass_rate_7d",
        "test_execution_features:flakiness_score",
    ]
).to_df()

# Use in training
X = training_df[[
    "execution_time_ms",
    "pass_rate_7d",
    "flakiness_score"
]]
y = training_df["target"]

model.fit(X, y)
```

**Using Features in Serving:**

```python
# inference_with_features.py
from feast import FeatureStore

store = FeatureStore(repo_path="feature_repo/")

def get_features_for_inference(test_id):
    """Get real-time features for test prediction."""
    
    # Get online features (< 10ms)
    feature_vector = store.get_online_features(
        features=[
            "test_execution_features:execution_time_ms",
            "test_execution_features:pass_rate_7d",
            "test_execution_features:flakiness_score",
        ],
        entity_rows=[{"test_id": test_id}]
    ).to_dict()
    
    return feature_vector

# Use in prediction
features = get_features_for_inference("test_001")
prediction = model.predict([features])
```

**Feature Materialization (Offline → Online):**

```bash
# Materialize features to online store
feast materialize-incremental $(date +%Y-%m-%d)

# Or in code
from feast import FeatureStore
from datetime import datetime, timedelta

store = FeatureStore(repo_path="feature_repo/")

# Materialize last 7 days
store.materialize_incremental(
    end_date=datetime.now()
)
```

---

## Data Versioning

### DVC (Data Version Control)

**Why DVC:**
- ✅ Version large datasets (GB/TB)
- ✅ Track data lineage
- ✅ Reproducible experiments
- ✅ Share data across team

**Setup:**

```bash
# Install DVC
pip install dvc[s3]==3.30.0

# Initialize DVC in your repo
cd /path/to/aiwebtest
dvc init

# Configure remote storage (S3/MinIO)
dvc remote add -d myremote s3://dvc-storage/aiwebtest
dvc remote modify myremote endpointurl http://localhost:9000
dvc remote modify myremote access_key_id minioadmin
dvc remote modify myremote secret_access_key minioadmin

# Commit DVC config
git add .dvc/config
git commit -m "Configure DVC remote storage"
```

**Tracking Data:**

```bash
# Track training data
dvc add data/training_experiences.parquet
dvc add data/test_results.csv
dvc add models/generation_agent_v1.pt

# This creates .dvc files
git add data/training_experiences.parquet.dvc
git add data/test_results.csv.dvc
git add models/generation_agent_v1.pt.dvc
git commit -m "Track training data and models"

# Push data to remote
dvc push

# Pull data from remote (on another machine)
dvc pull
```

**Creating Data Pipelines:**

```python
# dvc.yaml
stages:
  prepare_data:
    cmd: python scripts/prepare_data.py
    deps:
      - scripts/prepare_data.py
      - data/raw/experiences.json
    outs:
      - data/processed/training_data.parquet
    metrics:
      - data/processed/data_stats.json:
          cache: false
  
  train_model:
    cmd: python scripts/train.py --config configs/dqn.yaml
    deps:
      - scripts/train.py
      - data/processed/training_data.parquet
      - configs/dqn.yaml
    params:
      - configs/dqn.yaml:
          - learning_rate
          - batch_size
          - num_episodes
    outs:
      - models/dqn_model.pt
    metrics:
      - metrics/training_metrics.json:
          cache: false
    plots:
      - plots/reward_curve.csv:
          x: episode
          y: reward
  
  evaluate_model:
    cmd: python scripts/evaluate.py
    deps:
      - scripts/evaluate.py
      - models/dqn_model.pt
      - data/processed/test_data.parquet
    metrics:
      - metrics/evaluation_metrics.json:
          cache: false
```

**Running Pipeline:**

```bash
# Run entire pipeline
dvc repro

# Run specific stage
dvc repro train_model

# Show metrics
dvc metrics show

# Compare experiments
dvc metrics diff main workspace

# Show plots
dvc plots show
```

**Data Versioning Best Practices:**

```bash
# Tag data versions
git tag -a data-v1.0 -m "Initial training dataset"
git push origin data-v1.0

# Create experiment branch
git checkout -b experiment/new-reward-function
# ... modify data/code ...
dvc repro
git add .
git commit -m "Experiment with new reward function"
dvc push

# Compare with main branch
dvc metrics diff main
```

---

## A/B Testing Framework

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  A/B TESTING ARCHITECTURE                     │
└──────────────────────────────────────────────────────────────┘

User Request
      ↓
┌─────────────────┐
│ Load Balancer   │
│ (Nginx/Envoy)   │
└────────┬────────┘
         ↓
    [Traffic Split]
         ↓
    ┌────┴────┐
    ↓         ↓
Model A    Model B
(Control)  (Treatment)
80%        20%
    ↓         ↓
    └────┬────┘
         ↓
  Metrics Collection
    (Prometheus)
         ↓
  Statistical Analysis
  (Bayesian A/B Test)
         ↓
    Decision:
    - Continue
    - Promote Model B
    - Rollback
```

### Implementation

**1. Traffic Splitting with Nginx:**

```nginx
# nginx.conf
upstream model_a {
    server model-a-service:8000;
}

upstream model_b {
    server model-b-service:8000;
}

split_clients "${remote_addr}${http_user_agent}${date_gmt}" $model_upstream {
    80%     model_a;  # 80% to Model A (control)
    *       model_b;  # 20% to Model B (treatment)
}

server {
    listen 80;
    
    location /predict {
        proxy_pass http://$model_upstream;
        
        # Add model version header
        add_header X-Model-Version $model_upstream always;
        
        # Log for metrics
        access_log /var/log/nginx/ab_test.log ab_test_format;
    }
}

# Custom log format
log_format ab_test_format '$remote_addr - $remote_user [$time_local] '
                          '"$request" $status $body_bytes_sent '
                          '"$http_referer" "$http_user_agent" '
                          'model=$model_upstream response_time=$request_time';
```

**2. Application-Level Traffic Splitting:**

```python
# ab_test_router.py
import random
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any

class ModelVariant(Enum):
    CONTROL = "control"
    TREATMENT = "treatment"

@dataclass
class ABTestConfig:
    """A/B test configuration."""
    experiment_name: str
    control_model_path: str
    treatment_model_path: str
    treatment_percentage: float  # 0.0 to 1.0
    user_id_based: bool = True  # Consistent assignment
    enabled: bool = True

class ABTestRouter:
    """Routes requests to control or treatment models."""
    
    def __init__(self, config: ABTestConfig):
        self.config = config
        self.control_model = load_model(config.control_model_path)
        self.treatment_model = load_model(config.treatment_model_path)
        self.assignments = {}  # user_id -> variant (for consistency)
    
    def assign_variant(self, user_id: str) -> ModelVariant:
        """
        Assign user to control or treatment variant.
        
        Uses consistent hashing for user-based assignment.
        """
        if not self.config.enabled:
            return ModelVariant.CONTROL
        
        # Check if user already assigned
        if user_id in self.assignments:
            return self.assignments[user_id]
        
        # Assign based on user_id hash (consistent)
        if self.config.user_id_based:
            hash_value = hash(f"{self.config.experiment_name}:{user_id}")
            is_treatment = (hash_value % 100) < (self.config.treatment_percentage * 100)
        else:
            # Random assignment (not consistent)
            is_treatment = random.random() < self.config.treatment_percentage
        
        variant = ModelVariant.TREATMENT if is_treatment else ModelVariant.CONTROL
        
        # Store assignment
        if self.config.user_id_based:
            self.assignments[user_id] = variant
        
        return variant
    
    def predict(self, user_id: str, features: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction with assigned model variant."""
        variant = self.assign_variant(user_id)
        
        # Select model
        model = (self.treatment_model if variant == ModelVariant.TREATMENT 
                else self.control_model)
        
        # Predict
        prediction = model.predict(features)
        
        # Add metadata
        result = {
            "prediction": prediction,
            "variant": variant.value,
            "experiment": self.config.experiment_name,
            "user_id": user_id
        }
        
        # Log to metrics collector
        self.log_prediction(result)
        
        return result
    
    def log_prediction(self, result: Dict[str, Any]):
        """Log prediction for A/B test analysis."""
        # Send to Prometheus/metrics system
        ab_test_predictions.labels(
            experiment=result["experiment"],
            variant=result["variant"]
        ).inc()
```

**3. Metrics Collection:**

```python
# ab_test_metrics.py
from prometheus_client import Counter, Histogram, Gauge
import numpy as np
from scipy import stats

# Define metrics
ab_test_predictions = Counter(
    'ab_test_predictions_total',
    'Total predictions per variant',
    ['experiment', 'variant']
)

ab_test_latency = Histogram(
    'ab_test_prediction_latency_seconds',
    'Prediction latency per variant',
    ['experiment', 'variant'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

ab_test_accuracy = Gauge(
    'ab_test_accuracy',
    'Model accuracy per variant',
    ['experiment', 'variant']
)

ab_test_reward = Gauge(
    'ab_test_avg_reward',
    'Average reward per variant',
    ['experiment', 'variant']
)
```

**4. Statistical Analysis:**

```python
# ab_test_analysis.py
from scipy import stats
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class ABTestResults:
    """A/B test analysis results."""
    control_mean: float
    treatment_mean: float
    relative_improvement: float
    p_value: float
    confidence_interval_95: Tuple[float, float]
    statistical_significance: bool
    sample_size_control: int
    sample_size_treatment: int
    recommendation: str

class BayesianABTest:
    """
    Bayesian A/B testing for early stopping.
    
    More efficient than frequentist testing:
    - Can stop early if one variant is clearly better
    - Provides probability of superiority
    - Accounts for multiple comparisons
    """
    
    def __init__(self, prior_alpha=1, prior_beta=1):
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta
    
    def analyze(self, 
                control_successes: int,
                control_trials: int,
                treatment_successes: int,
                treatment_trials: int,
                min_probability=0.95) -> ABTestResults:
        """
        Perform Bayesian A/B test analysis.
        
        Args:
            control_successes: Number of successes in control
            control_trials: Total trials in control
            treatment_successes: Number of successes in treatment
            treatment_trials: Total trials in treatment
            min_probability: Minimum probability to declare winner (0.95 = 95%)
        
        Returns:
            ABTestResults with analysis
        """
        # Posterior distributions (Beta distribution)
        control_alpha = self.prior_alpha + control_successes
        control_beta = self.prior_beta + (control_trials - control_successes)
        
        treatment_alpha = self.prior_alpha + treatment_successes
        treatment_beta = self.prior_beta + (treatment_trials - treatment_successes)
        
        # Sample from posteriors
        n_samples = 100000
        control_samples = np.random.beta(control_alpha, control_beta, n_samples)
        treatment_samples = np.random.beta(treatment_alpha, treatment_beta, n_samples)
        
        # Calculate probability that treatment > control
        prob_treatment_better = np.mean(treatment_samples > control_samples)
        
        # Calculate expected lift
        control_mean = control_alpha / (control_alpha + control_beta)
        treatment_mean = treatment_alpha / (treatment_alpha + treatment_beta)
        relative_improvement = (treatment_mean - control_mean) / control_mean * 100
        
        # 95% credible interval for lift
        lift_samples = (treatment_samples - control_samples) / control_samples * 100
        ci_95 = np.percentile(lift_samples, [2.5, 97.5])
        
        # Recommendation
        if prob_treatment_better >= min_probability:
            recommendation = f"PROMOTE treatment (P={prob_treatment_better:.3f})"
        elif prob_treatment_better <= (1 - min_probability):
            recommendation = f"KEEP control (P={1-prob_treatment_better:.3f})"
        else:
            recommendation = f"CONTINUE testing (P={prob_treatment_better:.3f})"
        
        return ABTestResults(
            control_mean=control_mean,
            treatment_mean=treatment_mean,
            relative_improvement=relative_improvement,
            p_value=1 - prob_treatment_better,  # Approximate
            confidence_interval_95=tuple(ci_95),
            statistical_significance=(prob_treatment_better >= min_probability),
            sample_size_control=control_trials,
            sample_size_treatment=treatment_trials,
            recommendation=recommendation
        )
    
    def required_sample_size(self,
                            baseline_rate=0.1,
                            minimum_detectable_effect=0.1,
                            power=0.8,
                            alpha=0.05) -> int:
        """
        Calculate required sample size per variant.
        
        Args:
            baseline_rate: Current success rate (e.g., 0.1 = 10%)
            minimum_detectable_effect: Minimum relative improvement (e.g., 0.1 = 10%)
            power: Statistical power (1 - Type II error)
            alpha: Significance level (Type I error)
        
        Returns:
            Required sample size per variant
        """
        # Effect size (Cohen's h)
        p1 = baseline_rate
        p2 = baseline_rate * (1 + minimum_detectable_effect)
        effect_size = 2 * (np.arcsin(np.sqrt(p2)) - np.arcsin(np.sqrt(p1)))
        
        # Z-scores
        z_alpha = stats.norm.ppf(1 - alpha/2)
        z_beta = stats.norm.ppf(power)
        
        # Sample size per group
        n = ((z_alpha + z_beta) / effect_size) ** 2
        
        return int(np.ceil(n))

# Usage example
def analyze_ab_test():
    """Analyze A/B test results."""
    
    # Collect data from production
    control_data = get_metrics(variant="control")
    treatment_data = get_metrics(variant="treatment")
    
    # Initialize Bayesian A/B test
    ab_test = BayesianABTest()
    
    # Analyze
    results = ab_test.analyze(
        control_successes=control_data["successes"],
        control_trials=control_data["total"],
        treatment_successes=treatment_data["successes"],
        treatment_trials=treatment_data["total"],
        min_probability=0.95
    )
    
    # Print results
    print(f"""
    A/B Test Results:
    ================
    Control:    {results.control_mean:.3f} ({results.sample_size_control} samples)
    Treatment:  {results.treatment_mean:.3f} ({results.sample_size_treatment} samples)
    
    Relative Improvement: {results.relative_improvement:+.2f}%
    95% CI: [{results.confidence_interval_95[0]:.2f}%, {results.confidence_interval_95[1]:.2f}%]
    
    Statistical Significance: {results.statistical_significance}
    
    RECOMMENDATION: {results.recommendation}
    """)
    
    return results
```

**5. Gradual Rollout Automation:**

```python
# gradual_rollout.py
from dataclasses import dataclass
from typing import List
import time

@dataclass
class RolloutStage:
    """Single stage in gradual rollout."""
    percentage: float  # 0.0 to 1.0
    duration_seconds: int
    success_criteria: dict

class GradualRollout:
    """
    Manages gradual rollout of new model version.
    
    Stages:
    1. 5% for 6 hours
    2. 20% for 12 hours
    3. 50% for 24 hours
    4. 100% (full deployment)
    
    Automatic rollback if:
    - Error rate increases > 2x
    - Latency increases > 1.5x
    - Accuracy drops > 5%
    """
    
    def __init__(self, 
                 model_name: str,
                 new_version: str,
                 old_version: str):
        self.model_name = model_name
        self.new_version = new_version
        self.old_version = old_version
        
        # Define rollout stages
        self.stages = [
            RolloutStage(
                percentage=0.05,
                duration_seconds=6 * 3600,  # 6 hours
                success_criteria={
                    "max_error_rate_increase": 2.0,
                    "max_latency_increase": 1.5,
                    "min_accuracy": 0.85
                }
            ),
            RolloutStage(
                percentage=0.20,
                duration_seconds=12 * 3600,  # 12 hours
                success_criteria={
                    "max_error_rate_increase": 2.0,
                    "max_latency_increase": 1.5,
                    "min_accuracy": 0.87
                }
            ),
            RolloutStage(
                percentage=0.50,
                duration_seconds=24 * 3600,  # 24 hours
                success_criteria={
                    "max_error_rate_increase": 1.5,
                    "max_latency_increase": 1.3,
                    "min_accuracy": 0.90
                }
            ),
            RolloutStage(
                percentage=1.0,
                duration_seconds=None,  # Indefinite
                success_criteria={
                    "max_error_rate_increase": 1.2,
                    "max_latency_increase": 1.1,
                    "min_accuracy": 0.92
                }
            )
        ]
    
    def execute_rollout(self):
        """Execute gradual rollout with monitoring."""
        
        for i, stage in enumerate(self.stages):
            print(f"\n--- Stage {i+1}: {stage.percentage*100}% traffic ---")
            
            # Update traffic split
            self.update_traffic_split(stage.percentage)
            
            # Monitor for duration
            if stage.duration_seconds:
                success = self.monitor_stage(stage)
                
                if not success:
                    print("⚠️  Stage failed criteria. Rolling back...")
                    self.rollback()
                    return False
            
            print(f"✅ Stage {i+1} completed successfully")
        
        print("\n🎉 Gradual rollout completed successfully!")
        return True
    
    def update_traffic_split(self, percentage: float):
        """Update traffic split configuration."""
        # Update Nginx/load balancer configuration
        config = {
            "model_a": self.old_version,
            "model_b": self.new_version,
            "traffic_split": {
                "model_a": 1.0 - percentage,
                "model_b": percentage
            }
        }
        
        # Apply configuration (implementation depends on infrastructure)
        update_load_balancer_config(config)
        
        print(f"Traffic split updated: {percentage*100}% to new version")
    
    def monitor_stage(self, stage: RolloutStage) -> bool:
        """
        Monitor stage for success criteria.
        
        Checks every 5 minutes during stage duration.
        """
        start_time = time.time()
        check_interval = 300  # 5 minutes
        
        while time.time() - start_time < stage.duration_seconds:
            # Get metrics for both versions
            old_metrics = get_model_metrics(self.old_version)
            new_metrics = get_model_metrics(self.new_version)
            
            # Check success criteria
            checks = {
                "error_rate": (
                    new_metrics["error_rate"] / old_metrics["error_rate"]
                    <= stage.success_criteria["max_error_rate_increase"]
                ),
                "latency": (
                    new_metrics["latency_p95"] / old_metrics["latency_p95"]
                    <= stage.success_criteria["max_latency_increase"]
                ),
                "accuracy": (
                    new_metrics["accuracy"]
                    >= stage.success_criteria["min_accuracy"]
                )
            }
            
            # Check if any criteria failed
            if not all(checks.values()):
                print(f"❌ Criteria failed: {checks}")
                return False
            
            # Sleep until next check
            time.sleep(check_interval)
        
        return True
    
    def rollback(self):
        """Rollback to previous model version."""
        print(f"Rolling back to {self.old_version}...")
        
        # Set traffic to 100% old version
        self.update_traffic_split(0.0)
        
        # Optionally archive new version
        archive_model_version(self.model_name, self.new_version)
        
        # Send alert
        send_alert(
            title="Model Rollback",
            message=f"Rolled back {self.model_name} from {self.new_version} to {self.old_version}",
            severity="warning"
        )
```

**Usage:**

```python
# Deploy new model with gradual rollout
rollout = GradualRollout(
    model_name="generation-agent-dqn",
    new_version="v2.1.0",
    old_version="v2.0.5"
)

success = rollout.execute_rollout()

if success:
    # Promote to production in model registry
    promote_to_production("generation-agent-dqn", "v2.1.0")
```

---

---

## Drift Detection & Monitoring

### Types of Drift

```
┌──────────────────────────────────────────────────────────────┐
│                    TYPES OF DRIFT                             │
└──────────────────────────────────────────────────────────────┘

1. DATA DRIFT (Input Distribution Changes)
   - Feature distributions change over time
   - Example: Test complexity increases
   - Detection: KS test, PSI, Wasserstein distance

2. CONCEPT DRIFT (Input-Output Relationship Changes)
   - The relationship between features and target changes
   - Example: New testing patterns emerge
   - Detection: Accuracy degradation over time

3. PREDICTION DRIFT (Output Distribution Changes)
   - Model predictions distribution changes
   - Example: Confidence scores shift
   - Detection: Monitor prediction distributions

4. UPSTREAM DATA DRIFT
   - Changes in data pipeline/sources
   - Example: New test framework version
   - Detection: Schema validation, data quality checks
```

### Evidently AI Integration

**Installation:**

```bash
pip install evidently==0.4.10
```

**Data Drift Monitoring:**

```python
# drift_monitoring.py
from evidently import ColumnMapping
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, DataQualityPreset
from evidently.test_suite import TestSuite
from evidently.tests import *
import pandas as pd

class DriftMonitor:
    """
    Monitor data and concept drift using Evidently AI.
    
    Thresholds (Industry Standard 2025):
    - Data Drift PSI > 0.2: Investigate
    - Data Drift PSI > 0.3: Retrain
    - Accuracy Drop > 5%: Alert
    - Accuracy Drop > 10%: Auto-retrain
    """
    
    def __init__(self, reference_data: pd.DataFrame):
        """
        Initialize drift monitor with reference data.
        
        Args:
            reference_data: Baseline data from training/validation
        """
        self.reference_data = reference_data
        
        # Define column mapping
        self.column_mapping = ColumnMapping(
            target="target",
            prediction="prediction",
            numerical_features=[
                "execution_time_ms",
                "complexity_score",
                "confidence_score"
            ],
            categorical_features=[
                "test_type",
                "framework",
                "browser"
            ]
        )
    
    def detect_data_drift(self, current_data: pd.DataFrame) -> dict:
        """
        Detect data drift using statistical tests.
        
        Returns:
            Dict with drift metrics and recommendation
        """
        # Create drift report
        report = Report(metrics=[
            DataDriftPreset(),
            DataQualityPreset()
        ])
        
        report.run(
            reference_data=self.reference_data,
            current_data=current_data,
            column_mapping=self.column_mapping
        )
        
        # Extract metrics
        report_dict = report.as_dict()
        
        # Calculate PSI for each feature
        drift_scores = {}
        for feature in self.column_mapping.numerical_features:
            drift_score = self.calculate_psi(
                self.reference_data[feature],
                current_data[feature]
            )
            drift_scores[feature] = drift_score
        
        # Overall drift score (max PSI)
        max_drift = max(drift_scores.values())
        
        # Recommendation
        if max_drift > 0.3:
            recommendation = "CRITICAL: Immediate retraining required"
        elif max_drift > 0.2:
            recommendation = "WARNING: Schedule retraining soon"
        elif max_drift > 0.1:
            recommendation = "MONITOR: Elevated drift detected"
        else:
            recommendation = "OK: No significant drift"
        
        return {
            "drift_scores": drift_scores,
            "max_drift_score": max_drift,
            "recommendation": recommendation,
            "timestamp": pd.Timestamp.now(),
            "report": report_dict
        }
    
    def calculate_psi(self, expected: pd.Series, actual: pd.Series, buckets=10) -> float:
        """
        Calculate Population Stability Index (PSI).
        
        PSI Interpretation:
        - < 0.1: No significant change
        - 0.1 - 0.2: Moderate change
        - > 0.2: Significant change (action needed)
        
        Args:
            expected: Reference distribution
            actual: Current distribution
            buckets: Number of buckets for binning
        
        Returns:
            PSI score
        """
        # Create bins from expected
        breakpoints = np.linspace(
            expected.min(), expected.max(), buckets + 1
        )
        
        # Bin both distributions
        expected_percents = pd.cut(expected, breakpoints).value_counts(normalize=True).sort_index()
        actual_percents = pd.cut(actual, breakpoints).value_counts(normalize=True).sort_index()
        
        # Add small constant to avoid log(0)
        expected_percents = expected_percents + 0.0001
        actual_percents = actual_percents + 0.0001
        
        # Calculate PSI
        psi = np.sum(
            (actual_percents - expected_percents) * 
            np.log(actual_percents / expected_percents)
        )
        
        return psi
    
    def detect_concept_drift(self, current_data: pd.DataFrame, window_size=1000) -> dict:
        """
        Detect concept drift by monitoring accuracy over time.
        
        Args:
            current_data: Recent data with predictions and ground truth
            window_size: Rolling window for accuracy calculation
        
        Returns:
            Dict with concept drift metrics
        """
        # Calculate rolling accuracy
        current_data['correct'] = (
            current_data['prediction'] == current_data['target']
        ).astype(int)
        
        rolling_accuracy = (
            current_data['correct']
            .rolling(window=window_size)
            .mean()
        )
        
        # Baseline accuracy (first window)
        baseline_accuracy = rolling_accuracy.iloc[window_size]
        current_accuracy = rolling_accuracy.iloc[-1]
        
        # Calculate accuracy drop
        accuracy_drop = baseline_accuracy - current_accuracy
        relative_drop = accuracy_drop / baseline_accuracy * 100
        
        # Recommendation
        if relative_drop > 10:
            recommendation = "CRITICAL: Immediate retraining required"
        elif relative_drop > 5:
            recommendation = "WARNING: Schedule retraining"
        elif relative_drop > 2:
            recommendation = "MONITOR: Slight degradation"
        else:
            recommendation = "OK: Performance stable"
        
        return {
            "baseline_accuracy": baseline_accuracy,
            "current_accuracy": current_accuracy,
            "accuracy_drop_percent": relative_drop,
            "recommendation": recommendation,
            "timestamp": pd.Timestamp.now()
        }
    
    def generate_drift_report_html(self, current_data: pd.DataFrame, output_path="drift_report.html"):
        """Generate HTML drift report."""
        report = Report(metrics=[
            DataDriftPreset(),
            DataQualityPreset()
        ])
        
        report.run(
            reference_data=self.reference_data,
            current_data=current_data,
            column_mapping=self.column_mapping
        )
        
        report.save_html(output_path)
        print(f"Drift report saved to {output_path}")

# Automated drift monitoring
class ContinuousDriftMonitor:
    """
    Continuous drift monitoring with automated alerts.
    
    Runs every hour to check for drift.
    """
    
    def __init__(self, monitor: DriftMonitor):
        self.monitor = monitor
        self.drift_history = []
    
    def check_drift(self):
        """Check for drift and trigger actions."""
        # Get recent data
        current_data = fetch_recent_data(hours=24)
        
        # Detect data drift
        data_drift = self.monitor.detect_data_drift(current_data)
        
        # Detect concept drift
        concept_drift = self.monitor.detect_concept_drift(current_data)
        
        # Store in history
        self.drift_history.append({
            "timestamp": pd.Timestamp.now(),
            "data_drift": data_drift,
            "concept_drift": concept_drift
        })
        
        # Log metrics to Prometheus
        drift_psi_gauge.set(data_drift["max_drift_score"])
        accuracy_drop_gauge.set(concept_drift["accuracy_drop_percent"])
        
        # Check if retraining needed
        if (data_drift["max_drift_score"] > 0.3 or 
            concept_drift["accuracy_drop_percent"] > 10):
            
            # Trigger automated retraining
            trigger_retraining(
                reason="drift_detected",
                data_drift_score=data_drift["max_drift_score"],
                accuracy_drop=concept_drift["accuracy_drop_percent"]
            )
            
            # Send alert
            send_alert(
                title="Drift Detected - Retraining Triggered",
                message=f"""
                Data Drift PSI: {data_drift['max_drift_score']:.3f}
                Accuracy Drop: {concept_drift['accuracy_drop_percent']:.2f}%
                
                Automated retraining has been triggered.
                """,
                severity="high"
            )
        
        elif (data_drift["max_drift_score"] > 0.2 or 
              concept_drift["accuracy_drop_percent"] > 5):
            
            # Send warning
            send_alert(
                title="Drift Warning",
                message=data_drift["recommendation"],
                severity="medium"
            )
        
        return {
            "data_drift": data_drift,
            "concept_drift": concept_drift
        }

# Prometheus metrics
from prometheus_client import Gauge

drift_psi_gauge = Gauge(
    'model_drift_psi',
    'Population Stability Index for data drift',
    ['model_name', 'feature']
)

accuracy_drop_gauge = Gauge(
    'model_accuracy_drop_percent',
    'Percentage drop in model accuracy',
    ['model_name']
)
```

**Drift Detection Thresholds:**

| Metric | Threshold | Action |
|--------|-----------|--------|
| **PSI < 0.1** | OK | Continue monitoring |
| **PSI 0.1-0.2** | Monitor | Increase monitoring frequency |
| **PSI 0.2-0.3** | Warning | Schedule retraining within 48h |
| **PSI > 0.3** | Critical | **Immediate automated retraining** |
| **Accuracy Drop < 2%** | OK | Continue monitoring |
| **Accuracy Drop 2-5%** | Monitor | Investigate cause |
| **Accuracy Drop 5-10%** | Warning | Schedule retraining within 24h |
| **Accuracy Drop > 10%** | Critical | **Immediate automated retraining** |

---

## Automated Retraining Pipeline

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│           AUTOMATED RETRAINING PIPELINE                       │
└──────────────────────────────────────────────────────────────┘

Triggers:
├─ Scheduled (Weekly)
├─ Drift Detected (PSI > 0.3)
├─ Accuracy Drop (> 10%)
└─ Manual Request

      ↓
┌─────────────────┐
│ Data Collection │
│ - New experiences│
│ - Production logs│
│ - Labeled data  │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Data Validation │
│ (Great Expectations)
│ - Schema checks │
│ - Quality checks│
└────────┬────────┘
         ↓
┌─────────────────┐
│ Feature Eng.    │
│ (Feast)         │
│ - Generate features
│ - Store offline │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Model Training  │
│ (MLflow)        │
│ - Train model   │
│ - Log metrics   │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Model Validation│
│ - Test accuracy │
│ - A/B test prep │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Model Registry  │
│ - Register model│
│ - Tag for staging
└────────┬────────┘
         ↓
┌─────────────────┐
│ Approval        │
│ (Auto/Manual)   │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Gradual Rollout │
│ - 5% → 20% → 50% → 100%
│ - Monitor metrics
└─────────────────┘
```

### Airflow DAG Implementation

```python
# airflow_dags/automated_retraining.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.trigger_rule import TriggerRule
from datetime import datetime, timedelta
import pandas as pd

# Default arguments
default_args = {
    'owner': 'aiwebtest-ml-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email': ['ml-alerts@company.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Define DAG
dag = DAG(
    'automated_model_retraining',
    default_args=default_args,
    description='Automated model retraining pipeline',
    schedule_interval='@weekly',  # Weekly schedule
    catchup=False,
    tags=['ml', 'retraining', 'production']
)

def check_retraining_triggers(**context):
    """
    Check if retraining should be triggered.
    
    Triggers:
    1. Scheduled (weekly)
    2. Drift detected (PSI > 0.3)
    3. Accuracy drop (> 10%)
    4. Manual request
    """
    # Get recent drift metrics
    drift_monitor = DriftMonitor(reference_data=load_reference_data())
    current_data = fetch_recent_data(days=7)
    
    drift_results = drift_monitor.detect_data_drift(current_data)
    concept_drift = drift_monitor.detect_concept_drift(current_data)
    
    # Check triggers
    should_retrain = (
        context['dag_run'].external_trigger or  # Manual trigger
        drift_results['max_drift_score'] > 0.3 or  # Data drift
        concept_drift['accuracy_drop_percent'] > 10  # Concept drift
    )
    
    if should_retrain:
        context['task_instance'].xcom_push(
            key='retrain_reason',
            value={
                'drift_score': drift_results['max_drift_score'],
                'accuracy_drop': concept_drift['accuracy_drop_percent'],
                'manual': context['dag_run'].external_trigger
            }
        )
    
    return should_retrain

def collect_training_data(**context):
    """Collect new training data from production."""
    # Fetch new experiences from production
    new_data = fetch_production_experiences(days=7)
    
    # Combine with existing training data (sliding window)
    existing_data = load_training_data()
    combined_data = pd.concat([existing_data, new_data]).tail(1000000)  # Keep last 1M
    
    # Save to DVC
    save_path = f"data/training/experiences_{datetime.now().strftime('%Y%m%d')}.parquet"
    combined_data.to_parquet(save_path)
    
    # Track with DVC
    os.system(f"dvc add {save_path}")
    os.system(f"git add {save_path}.dvc")
    
    context['task_instance'].xcom_push(key='training_data_path', value=save_path)
    
    return save_path

def validate_data(**context):
    """Validate data quality using Great Expectations."""
    data_path = context['task_instance'].xcom_pull(
        task_ids='collect_training_data',
        key='training_data_path'
    )
    
    data = pd.read_parquet(data_path)
    
    # Create Great Expectations suite
    from great_expectations.dataset import PandasDataset
    
    ge_df = PandasDataset(data)
    
    # Define expectations
    ge_df.expect_table_row_count_to_be_between(min_value=100000, max_value=2000000)
    ge_df.expect_column_values_to_not_be_null('state')
    ge_df.expect_column_values_to_not_be_null('action')
    ge_df.expect_column_values_to_not_be_null('reward')
    ge_df.expect_column_values_to_be_between('reward', min_value=-100, max_value=100)
    
    # Validate
    results = ge_df.validate()
    
    if not results['success']:
        raise ValueError(f"Data validation failed: {results}")
    
    return True

def train_model(**context):
    """Train new model version."""
    import mlflow
    
    data_path = context['task_instance'].xcom_pull(
        task_ids='collect_training_data',
        key='training_data_path'
    )
    
    # Load data
    data = pd.read_parquet(data_path)
    
    # Set MLflow experiment
    mlflow.set_tracking_uri("http://mlflow:5000")
    mlflow.set_experiment("automated-retraining")
    
    with mlflow.start_run(run_name=f"auto_retrain_{datetime.now().strftime('%Y%m%d_%H%M')}"):
        # Log trigger reason
        retrain_reason = context['task_instance'].xcom_pull(
            task_ids='check_triggers',
            key='retrain_reason'
        )
        mlflow.log_params(retrain_reason)
        
        # Train model
        model = train_dqn_model(data)
        
        # Log model
        mlflow.pytorch.log_model(
            pytorch_model=model,
            artifact_path="model",
            registered_model_name="generation-agent-dqn"
        )
        
        # Get run ID for model registration
        run_id = mlflow.active_run().info.run_id
        
        context['task_instance'].xcom_push(key='mlflow_run_id', value=run_id)
        
        return run_id

def validate_model(**context):
    """Validate new model performance."""
    run_id = context['task_instance'].xcom_pull(
        task_ids='train_model',
        key='mlflow_run_id'
    )
    
    # Load model
    model = mlflow.pytorch.load_model(f"runs:/{run_id}/model")
    
    # Evaluate on validation set
    val_data = load_validation_data()
    metrics = evaluate_model(model, val_data)
    
    # Compare with current production model
    prod_model = load_production_model("generation-agent-dqn")
    prod_metrics = evaluate_model(prod_model, val_data)
    
    # Check if new model is better
    is_better = metrics['accuracy'] > prod_metrics['accuracy']
    improvement = (metrics['accuracy'] - prod_metrics['accuracy']) / prod_metrics['accuracy'] * 100
    
    if not is_better:
        raise ValueError(
            f"New model not better than production. "
            f"Accuracy: {metrics['accuracy']:.3f} vs {prod_metrics['accuracy']:.3f}"
        )
    
    context['task_instance'].xcom_push(
        key='model_improvement',
        value={'improvement_percent': improvement, 'new_accuracy': metrics['accuracy']}
    )
    
    return True

def register_and_promote(**context):
    """Register model and promote to staging."""
    run_id = context['task_instance'].xcom_pull(
        task_ids='train_model',
        key='mlflow_run_id'
    )
    
    # Register model
    version_manager = ModelVersionManager("generation-agent-dqn")
    model_version, semantic_version = version_manager.create_version(
        run_id=run_id,
        version_type="minor"  # Automated retraining = minor version
    )
    
    # Promote to staging
    promote_to_staging("generation-agent-dqn", model_version.version)
    
    context['task_instance'].xcom_push(
        key='model_version',
        value={'version': model_version.version, 'semantic_version': semantic_version}
    )
    
    return model_version.version

def trigger_gradual_rollout(**context):
    """Trigger gradual rollout DAG."""
    model_version = context['task_instance'].xcom_pull(
        task_ids='register_promote',
        key='model_version'
    )
    
    # Trigger rollout DAG
    return {
        'model_name': 'generation-agent-dqn',
        'new_version': model_version['semantic_version'],
        'old_version': get_current_production_version()
    }

def send_completion_notification(**context):
    """Send notification about retraining completion."""
    model_version = context['task_instance'].xcom_pull(
        task_ids='register_promote',
        key='model_version'
    )
    improvement = context['task_instance'].xcom_pull(
        task_ids='validate_model',
        key='model_improvement'
    )
    
    send_slack_message(
        channel='#ml-ops',
        message=f"""
        ✅ Automated Retraining Complete
        
        Model: generation-agent-dqn
        New Version: {model_version['semantic_version']}
        Improvement: +{improvement['improvement_percent']:.2f}%
        New Accuracy: {improvement['new_accuracy']:.3f}
        
        Gradual rollout initiated (5% → 20% → 50% → 100%)
        """
    )

# Define tasks
check_triggers = PythonOperator(
    task_id='check_triggers',
    python_callable=check_retraining_triggers,
    dag=dag
)

collect_data = PythonOperator(
    task_id='collect_training_data',
    python_callable=collect_training_data,
    dag=dag
)

validate_data_task = PythonOperator(
    task_id='validate_data',
    python_callable=validate_data,
    dag=dag
)

train = PythonOperator(
    task_id='train_model',
    python_callable=train_model,
    dag=dag
)

validate = PythonOperator(
    task_id='validate_model',
    python_callable=validate_model,
    dag=dag
)

register_promote = PythonOperator(
    task_id='register_promote',
    python_callable=register_and_promote,
    dag=dag
)

rollout = TriggerDagRunOperator(
    task_id='trigger_rollout',
    trigger_dag_id='gradual_rollout',
    conf='{{ task_instance.xcom_pull(task_ids="register_promote", key="model_version") }}',
    dag=dag
)

notify = PythonOperator(
    task_id='notify',
    python_callable=send_completion_notification,
    trigger_rule=TriggerRule.ALL_SUCCESS,
    dag=dag
)

# Define task dependencies
check_triggers >> collect_data >> validate_data_task >> train >> validate >> register_promote >> rollout >> notify
```

---

## Model Governance

### Approval Workflows

```
┌──────────────────────────────────────────────────────────────┐
│              MODEL APPROVAL WORKFLOW                          │
└──────────────────────────────────────────────────────────────┘

New Model Trained
        ↓
   Automatic Checks
   ├─ Accuracy > threshold
   ├─ No bias detected
   ├─ Latency < SLA
   └─ Security scan passed
        ↓
   [PASS] ────────┐
        ↓         ↓
   Low Risk?  High Risk?
        ↓         ↓
   Auto-Approve  Manual Review
        ↓         ↓
        └────┬────┘
             ↓
        Staging
             ↓
        A/B Test
             ↓
       [Success?]
             ↓
        Production
```

**Governance Rules:**

```python
# model_governance.py
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_REVIEW = "requires_review"

@dataclass
class GovernancePolicy:
    """Model governance policy."""
    
    # Automatic approval criteria
    min_accuracy: float = 0.90
    max_latency_ms: float = 100
    min_improvement_percent: float = 2.0  # vs current production
    
    # Risk thresholds
    high_risk_accuracy_drop: float = 0.05  # 5% drop = high risk
    high_risk_new_architecture: bool = True  # New arch = high risk
    
    # Required approvers
    auto_approve_low_risk: bool = True
    required_approvers_high_risk: List[str] = None
    
    def __post_init__(self):
        if self.required_approvers_high_risk is None:
            self.required_approvers_high_risk = [
                "ml-lead@company.com",
                "qa-lead@company.com"
            ]

class ModelGovernance:
    """Manages model approval workflows."""
    
    def __init__(self, policy: GovernancePolicy):
        self.policy = policy
        self.client = MlflowClient()
    
    def evaluate_for_approval(self, model_name: str, version: int) -> ApprovalStatus:
        """
        Evaluate model for automatic approval.
        
        Returns approval status based on governance policy.
        """
        # Get model metadata
        model_version = self.client.get_model_version(model_name, version)
        
        # Get model metrics
        run = self.client.get_run(model_version.run_id)
        metrics = run.data.metrics
        
        # Get current production metrics
        prod_version = self.client.get_latest_versions(model_name, stages=["Production"])[0]
        prod_run = self.client.get_run(prod_version.run_id)
        prod_metrics = prod_run.data.metrics
        
        # Automatic checks
        checks = {
            "accuracy_threshold": metrics['accuracy'] >= self.policy.min_accuracy,
            "latency_threshold": metrics['latency_p95_ms'] <= self.policy.max_latency_ms,
            "improvement": (
                (metrics['accuracy'] - prod_metrics['accuracy']) / prod_metrics['accuracy'] * 100
                >= self.policy.min_improvement_percent
            )
        }
        
        # Risk assessment
        is_high_risk = (
            # Large accuracy drop from baseline
            (prod_metrics['accuracy'] - metrics['accuracy']) > self.policy.high_risk_accuracy_drop or
            # New architecture
            (self.policy.high_risk_new_architecture and 
             model_version.tags.get('architecture_change') == 'true')
        )
        
        # Determine status
        if not all(checks.values()):
            return ApprovalStatus.REJECTED
        elif is_high_risk:
            return ApprovalStatus.REQUIRES_REVIEW
        elif self.policy.auto_approve_low_risk:
            return ApprovalStatus.APPROVED
        else:
            return ApprovalStatus.REQUIRES_REVIEW
    
    def request_approval(self, model_name: str, version: int):
        """Request manual approval for high-risk model."""
        # Create approval request
        approval_request = {
            "model_name": model_name,
            "version": version,
            "requested_at": datetime.now().isoformat(),
            "approvers": self.policy.required_approvers_high_risk,
            "status": "pending"
        }
        
        # Send notifications
        for approver in self.policy.required_approvers_high_risk:
            send_approval_request_email(
                to=approver,
                model_name=model_name,
                version=version,
                approval_url=f"https://mlops.company.com/approvals/{model_name}/{version}"
            )
        
        # Tag model version
        self.client.set_model_version_tag(
            name=model_name,
            version=version,
            key="approval_status",
            value="pending_review"
        )
    
    def approve_model(self, model_name: str, version: int, approver: str, comments: str = ""):
        """Approve model for production deployment."""
        # Update model version tags
        self.client.set_model_version_tag(
            name=model_name,
            version=version,
            key="approval_status",
            value="approved"
        )
        
        self.client.set_model_version_tag(
            name=model_name,
            version=version,
            key="approved_by",
            value=approver
        )
        
        self.client.set_model_version_tag(
            name=model_name,
            version=version,
            key="approved_at",
            value=datetime.now().isoformat()
        )
        
        if comments:
            self.client.set_model_version_tag(
                name=model_name,
                version=version,
                key="approval_comments",
                value=comments
            )
        
        # Log audit event
        log_audit_event(
            event_type="model_approved",
            model_name=model_name,
            version=version,
            user=approver,
            timestamp=datetime.now()
        )
        
        # Promote to staging (ready for A/B test)
        promote_to_staging(model_name, version)
```

### Model Cards

Document each model version with standardized model cards:

```python
# model_card.py
from dataclasses import dataclass, asdict
from typing import List, Dict
import yaml

@dataclass
class ModelCard:
    """
    Standardized model documentation.
    
    Based on: https://arxiv.org/abs/1810.03993
    """
    # Model Details
    model_name: str
    version: str
    date: str
    model_type: str  # e.g., "DQN", "Dueling DQN"
    framework: str  # e.g., "PyTorch 2.1"
    
    # Intended Use
    intended_use: str
    primary_users: List[str]
    out_of_scope: List[str]
    
    # Training Data
    training_data_source: str
    training_data_size: int
    data_date_range: str
    feature_list: List[str]
    
    # Model Performance
    metrics: Dict[str, float]
    test_data_performance: Dict[str, float]
    
    # Ethical Considerations
    bias_analysis: str
    limitations: List[str]
    
    # Deployment
    deployment_platform: str
    monitoring_metrics: List[str]
    retraining_policy: str
    
    def save(self, path: str):
        """Save model card to YAML file."""
        with open(path, 'w') as f:
            yaml.dump(asdict(self), f, default_flow_style=False)
    
    @classmethod
    def load(cls, path: str):
        """Load model card from YAML file."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)

# Example model card
generation_agent_card = ModelCard(
    model_name="generation-agent-dqn",
    version="2.1.0",
    date="2025-10-27",
    model_type="Dueling Double DQN",
    framework="PyTorch 2.1.0",
    
    intended_use="Generate test cases from requirements for web applications",
    primary_users=["QA Engineers", "Test Automation Engineers"],
    out_of_scope=[
        "Mobile app testing",
        "Performance testing",
        "Security testing"
    ],
    
    training_data_source="Production test execution logs + synthetic data",
    training_data_size=1_000_000,
    data_date_range="2024-01-01 to 2025-10-01",
    feature_list=[
        "requirement_text_embedding",
        "ui_complexity_score",
        "historical_test_coverage",
        "previous_agent_confidence"
    ],
    
    metrics={
        "accuracy": 0.93,
        "precision": 0.91,
        "recall": 0.89,
        "f1_score": 0.90,
        "avg_reward": 85.3
    },
    
    test_data_performance={
        "accuracy": 0.91,
        "latency_p95_ms": 45,
        "throughput_qps": 500
    },
    
    bias_analysis="No significant bias detected across different UI frameworks. Slightly lower performance on complex SPAs (87% vs 93% average).",
    limitations=[
        "Limited to web applications built with standard frameworks",
        "May struggle with highly dynamic UIs",
        "Requires clear requirements (unclear requirements = lower accuracy)"
    ],
    
    deployment_platform="Kubernetes on AWS EKS",
    monitoring_metrics=[
        "accuracy_rolling_7d",
        "latency_p95",
        "drift_psi",
        "error_rate"
    ],
    retraining_policy="Automated retraining weekly or when drift PSI > 0.3"
)

generation_agent_card.save("models/generation-agent-dqn-v2.1.0-card.yaml")
```

---

## CI/CD for ML

### GitHub Actions Pipeline

```yaml
# .github/workflows/ml-pipeline.yml
name: ML Pipeline - Train, Test, Deploy

on:
  push:
    branches: [main, develop]
    paths:
      - 'src/**'
      - 'configs/**'
      - 'data/**'
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM
  workflow_dispatch:  # Manual trigger

env:
  MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_TRACKING_URI }}
  AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
  AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}

jobs:
  
  # Stage 1: Code Quality
  code-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      
      - name: Lint with flake8
        run: |
          flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
      
      - name: Type check with mypy
        run: |
          mypy src/
      
      - name: Format check with black
        run: |
          black --check src/
  
  # Stage 2: Unit Tests
  unit-tests:
    runs-on: ubuntu-latest
    needs: code-quality
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run unit tests
        run: |
          pytest tests/unit/ --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
  
  # Stage 3: Data Validation
  data-validation:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install great_expectations
      
      - name: Pull data with DVC
        run: |
          pip install dvc[s3]
          dvc pull data/processed/training_data.parquet
      
      - name: Validate data
        run: |
          python scripts/validate_data.py
  
  # Stage 4: Model Training
  train-model:
    runs-on: ubuntu-latest
    needs: data-validation
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Pull training data
        run: |
          pip install dvc[s3]
          dvc pull
      
      - name: Train model
        run: |
          python scripts/train.py --config configs/dqn.yaml
      
      - name: Upload model artifacts
        uses: actions/upload-artifact@v3
        with:
          name: trained-model
          path: models/
  
  # Stage 5: Model Evaluation
  evaluate-model:
    runs-on: ubuntu-latest
    needs: train-model
    steps:
      - uses: actions/checkout@v3
      
      - name: Download model
        uses: actions/download-artifact@v3
        with:
          name: trained-model
          path: models/
      
      - name: Evaluate model
        run: |
          python scripts/evaluate.py --model models/dqn_model.pt
      
      - name: Check performance thresholds
        run: |
          python scripts/check_thresholds.py \
            --min-accuracy 0.85 \
            --max-latency 100
  
  # Stage 6: Register Model
  register-model:
    runs-on: ubuntu-latest
    needs: evaluate-model
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Register model in MLflow
        run: |
          python scripts/register_model.py \
            --model-name generation-agent-dqn \
            --stage Staging
  
  # Stage 7: Deploy to Staging
  deploy-staging:
    runs-on: ubuntu-latest
    needs: register-model
    environment: staging
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure kubectl
        run: |
          echo "${{ secrets.KUBECONFIG }}" > kubeconfig
          export KUBECONFIG=kubeconfig
      
      - name: Deploy to staging
        run: |
          kubectl set image deployment/generation-agent \
            generation-agent=aiwebtest/generation-agent:${{ github.sha }} \
            -n staging
      
      - name: Wait for rollout
        run: |
          kubectl rollout status deployment/generation-agent -n staging
  
  # Stage 8: Integration Tests
  integration-tests:
    runs-on: ubuntu-latest
    needs: deploy-staging
    steps:
      - uses: actions/checkout@v3
      
      - name: Run integration tests
        run: |
          pytest tests/integration/ --staging-url=${{ secrets.STAGING_URL }}
  
  # Stage 9: Deploy to Production (Manual Approval)
  deploy-production:
    runs-on: ubuntu-latest
    needs: integration-tests
    environment: production
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Promote model to production
        run: |
          python scripts/promote_model.py \
            --model-name generation-agent-dqn \
            --to-stage Production
      
      - name: Trigger gradual rollout
        run: |
          python scripts/trigger_rollout.py \
            --model-name generation-agent-dqn \
            --new-version ${{ github.sha }}
```

---

## Implementation Roadmap

### Timeline: 15 Days (3 Weeks)

```
Week 1: Foundation (Days 1-5)
┌─────────────────────────────────────────────┐
│ Day 1-2: MLflow Setup                       │
│ - Install MLflow server                     │
│ - Configure PostgreSQL + MinIO              │
│ - Test experiment tracking                  │
│                                             │
│ Day 3: Model Registry                       │
│ - Set up model registry                     │
│ - Implement versioning logic                │
│ - Test model promotion workflow             │
│                                             │
│ Day 4-5: Feature Store (Feast)              │
│ - Install Feast                             │
│ - Define feature views                      │
│ - Implement offline→online materialization  │
└─────────────────────────────────────────────┘

Week 2: Monitoring & Automation (Days 6-10)
┌─────────────────────────────────────────────┐
│ Day 6-7: Drift Detection                    │
│ - Install Evidently AI                      │
│ - Implement PSI monitoring                  │
│ - Set up drift alerts                       │
│                                             │
│ Day 8-9: A/B Testing Framework              │
│ - Configure Nginx traffic splitting         │
│ - Implement application-level routing       │
│ - Set up metrics collection                 │
│                                             │
│ Day 10: Data Versioning (DVC)               │
│ - Install DVC                               │
│ - Track datasets                            │
│ - Create data pipelines                     │
└─────────────────────────────────────────────┘

Week 3: Governance & CI/CD (Days 11-15)
┌─────────────────────────────────────────────┐
│ Day 11-12: Automated Retraining             │
│ - Create Airflow DAGs                       │
│ - Implement retraining pipeline             │
│ - Test end-to-end automation                │
│                                             │
│ Day 13: Model Governance                    │
│ - Implement approval workflows              │
│ - Create model cards                        │
│ - Set up audit logging                      │
│                                             │
│ Day 14-15: CI/CD Pipeline                   │
│ - Create GitHub Actions workflows           │
│ - Integrate all MLOps components            │
│ - End-to-end testing                        │
└─────────────────────────────────────────────┘
```

### Success Metrics

**By End of Week 1:**
- ✅ All experiments tracked in MLflow
- ✅ Models registered with semantic versioning
- ✅ Features served from Feast (<10ms latency)

**By End of Week 2:**
- ✅ Drift detection running hourly
- ✅ A/B testing framework operational
- ✅ All datasets version-controlled with DVC

**By End of Week 3:**
- ✅ Automated retraining pipeline functional
- ✅ Model governance workflows in place
- ✅ Full CI/CD pipeline operational

---

## Summary & Next Steps

### What We've Built

This comprehensive MLOps architecture provides:

1. ✅ **Experiment Tracking** - MLflow with PostgreSQL + MinIO
2. ✅ **Model Registry** - Semantic versioning + lifecycle management
3. ✅ **Feature Store** - Feast for training/serving consistency
4. ✅ **Data Versioning** - DVC for reproducibility
5. ✅ **A/B Testing** - Gradual rollout with Bayesian analysis
6. ✅ **Drift Detection** - Evidently AI with automated alerts
7. ✅ **Automated Retraining** - Airflow DAGs with smart triggers
8. ✅ **Model Governance** - Approval workflows + model cards
9. ✅ **CI/CD for ML** - GitHub Actions end-to-end pipeline

### Integration with Existing Docs

This MLOps architecture integrates with:
- **PRD**: Fulfills FR-26, FR-27 (AI Model Management)
- **SRS**: Extends technical stack with MLOps tools
- **RL Architecture**: Provides production infrastructure for RL models
- **Multi-GPU Setup**: Supports distributed training in CI/CD

### Next Actions

1. **Review** this MLOps architecture document
2. **Integrate** MLOps sections into existing PRD/SRS
3. **Update** implementation timeline in PRD (add 15-day MLOps phase)
4. **Begin** Week 1 implementation (MLflow + Model Registry)

---

**Document Complete!** 🎉

This addresses the critical MLOps maturity gap with industry best practices for 2025.


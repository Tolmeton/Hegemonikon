#!/bin/bash
# ============================================================
# Vertex AI Vector Search — GCP 自動セットアップ
# Phase 2 of Grand Search Architecture
# ============================================================
#
# Usage:
#   bash scripts/vector_search_setup.sh [step]
#
# Steps:
#   1 - Enable APIs
#   2 - Create GCS bucket
#   3 - Export vectors from FAISS → GCS (JSONL)
#   4 - Create Vector Search Index
#   5 - Create Index Endpoint
#   6 - Deploy Index to Endpoint
#   all - Run all steps (default)
#
# Prerequisites:
#   - gcloud CLI authenticated
#   - Python .venv with faiss-cpu, google-cloud-aiplatform
# ============================================================

set -euo pipefail

# ── Configuration ──
PROJECT_ID="project-d4c65f26-e7d2-44af-841"
REGION="us-central1"
ACCOUNT="movement8426@gmail.com"
BUCKET_NAME="gs://${PROJECT_ID}-vector-data"
INDEX_DISPLAY_NAME="periskope-knowledge-3072d"
ENDPOINT_DISPLAY_NAME="periskope-vs-endpoint"
DIMENSIONS=3072
DISTANCE_MEASURE="COSINE_DISTANCE"     # DOT_PRODUCT_DISTANCE, COSINE_DISTANCE, SQUARED_L2_DISTANCE
SHARD_SIZE="SHARD_SIZE_SMALL"           # Minimum (≤100K vectors)
MACHINE_TYPE="e2-standard-2"            # $0.094/node-hour ≈ $68/month

# Paths
HGK_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXPORT_DIR="/tmp/vector_search_export"
EXPORT_FILE="${EXPORT_DIR}/vectors.json"

# ── Helper functions ──
log() { echo "[$(date +%H:%M:%S)] $*"; }
err() { echo "[ERROR] $*" >&2; exit 1; }

check_gcloud() {
    command -v gcloud >/dev/null 2>&1 || err "gcloud CLI not found"
    gcloud config set project "$PROJECT_ID" 2>/dev/null
    gcloud config set account "$ACCOUNT" 2>/dev/null
    log "GCP: project=$PROJECT_ID account=$ACCOUNT region=$REGION"
}

# ── Step 1: Enable APIs ──
step_enable_apis() {
    log "Step 1: Enabling APIs..."
    gcloud services enable aiplatform.googleapis.com \
        --project="$PROJECT_ID" 2>/dev/null
    gcloud services enable storage.googleapis.com \
        --project="$PROJECT_ID" 2>/dev/null
    log "Step 1: APIs enabled ✓"
}

# ── Step 2: Create GCS Bucket ──
step_create_bucket() {
    log "Step 2: Creating GCS bucket..."
    if gsutil ls "$BUCKET_NAME" 2>/dev/null; then
        log "Step 2: Bucket already exists ✓"
    else
        gsutil mb -p "$PROJECT_ID" -l "$REGION" "$BUCKET_NAME"
        log "Step 2: Bucket created ✓"
    fi
}

# ── Step 3: Export Vectors from FAISS → GCS ──
step_export_vectors() {
    log "Step 3: Exporting vectors from FAISS..."
    mkdir -p "$EXPORT_DIR"

    cd "$HGK_ROOT"
    PYTHONPATH=. .venv/bin/python -u -c "
import json
import sys
sys.path.insert(0, '${HGK_ROOT}')

from mekhane.anamnesis.index import GnosisIndex

EXPORT_FILE = '${EXPORT_FILE}'
DIMS = ${DIMENSIONS}

# Sources to include in Vector Search (static/semi-static knowledge)
INCLUDE_SOURCES = {
    'semantic_scholar', 'arxiv', 'ki', 'kernel', 'workflow',
    'review', 'research', 'xseries', 'doxa', 'step'
}
# Exclude: session (30K, real-time), handoff (7.5K, real-time), rom, conversation

idx = GnosisIndex()
records = idx._backend.to_list()
print(f'FAISS records: {len(records)}', file=sys.stderr)

count = 0
skipped = 0

with open(EXPORT_FILE, 'w') as f:
    for row in records:
        source = str(row.get('source', '')).lower()

        # Filter by source
        if source and source not in INCLUDE_SOURCES:
            skipped += 1
            continue

        # Get vector
        vector = row.get('vector', row.get('embedding', None))
        if vector is None:
            skipped += 1
            continue

        # Convert to list if numpy array
        if hasattr(vector, 'tolist'):
            vector = vector.tolist()

        if len(vector) != DIMS:
            skipped += 1
            continue

        # Build metadata restricts (for filtering)
        doc_id = str(row.get('primary_key', row.get('id', row.get('doc_id', f'faiss_{count}'))))
        source_val = source or 'knowledge'

        record = {
            'id': doc_id,
            'embedding': vector,
            'restricts': [
                {'namespace': 'source', 'allow': [source_val]},
            ],
            'crowding_tag': source_val,
        }
        f.write(json.dumps(record) + '\n')
        count += 1

print(f'Exported {count} vectors, skipped {skipped}', file=sys.stderr)
print(f'File: {EXPORT_FILE}', file=sys.stderr)
"

    if [ ! -f "$EXPORT_FILE" ] || [ ! -s "$EXPORT_FILE" ]; then
        err "Export failed — no vectors exported"
    fi

    VECTOR_COUNT=$(wc -l < "$EXPORT_FILE")
    log "Step 3: Exported $VECTOR_COUNT vectors to $EXPORT_FILE"

    # Upload to GCS
    log "Step 3: Uploading to GCS..."
    gsutil -m cp "$EXPORT_FILE" "${BUCKET_NAME}/vectors/"
    log "Step 3: Upload complete ✓"
}

# ── Step 4: Create Vector Search Index ──
step_create_index() {
    log "Step 4: Creating Vector Search Index..."

    # Check if index already exists
    EXISTING=$(gcloud ai indexes list \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --filter="displayName=${INDEX_DISPLAY_NAME}" \
        --format="value(name)" 2>/dev/null || true)

    if [ -n "$EXISTING" ]; then
        log "Step 4: Index already exists: $EXISTING"
        INDEX_ID=$(echo "$EXISTING" | awk -F'/' '{print $NF}')
        echo "$INDEX_ID" > "${EXPORT_DIR}/index_id.txt"
        return
    fi

    # Create metadata JSON for index configuration
    cat > "${EXPORT_DIR}/index_metadata.json" <<EOF
{
  "contentsDeltaUri": "${BUCKET_NAME}/vectors/",
  "config": {
    "dimensions": ${DIMENSIONS},
    "approximateNeighborsCount": 50,
    "distanceMeasureType": "${DISTANCE_MEASURE}",
    "featureNormType": "UNIT_L2_NORM",
    "shardSize": "${SHARD_SIZE}",
    "algorithmConfig": {
      "treeAhConfig": {
        "leafNodeEmbeddingCount": 500,
        "fractionLeafNodesToSearch": 0.05
      }
    }
  }
}
EOF

    gcloud ai indexes create \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --display-name="$INDEX_DISPLAY_NAME" \
        --description="Periskopē internal knowledge vectors (3072d, papers/KI/kernel)" \
        --metadata-file="${EXPORT_DIR}/index_metadata.json" \
        --format="value(name)" 2>&1 | tee "${EXPORT_DIR}/index_create.log"

    log "Step 4: Index creation initiated (this takes 10-30 minutes) ✓"
    log "  Monitor: gcloud ai indexes list --project=$PROJECT_ID --region=$REGION"
}

# ── Step 5: Create Index Endpoint ──
step_create_endpoint() {
    log "Step 5: Creating Index Endpoint..."

    EXISTING=$(gcloud ai index-endpoints list \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --filter="displayName=${ENDPOINT_DISPLAY_NAME}" \
        --format="value(name)" 2>/dev/null || true)

    if [ -n "$EXISTING" ]; then
        log "Step 5: Endpoint already exists: $EXISTING"
        ENDPOINT_ID=$(echo "$EXISTING" | awk -F'/' '{print $NF}')
        echo "$ENDPOINT_ID" > "${EXPORT_DIR}/endpoint_id.txt"
        return
    fi

    gcloud ai index-endpoints create \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --display-name="$ENDPOINT_DISPLAY_NAME" \
        --description="Periskopē Vector Search endpoint" \
        --format="value(name)" 2>&1 | tee "${EXPORT_DIR}/endpoint_create.log"

    log "Step 5: Endpoint creation initiated ✓"
}

# ── Step 6: Deploy Index to Endpoint ──
step_deploy_index() {
    log "Step 6: Deploying Index to Endpoint..."

    # Get IDs
    INDEX_RESOURCE=$(gcloud ai indexes list \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --filter="displayName=${INDEX_DISPLAY_NAME}" \
        --format="value(name)" 2>/dev/null)

    ENDPOINT_RESOURCE=$(gcloud ai index-endpoints list \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --filter="displayName=${ENDPOINT_DISPLAY_NAME}" \
        --format="value(name)" 2>/dev/null)

    if [ -z "$INDEX_RESOURCE" ] || [ -z "$ENDPOINT_RESOURCE" ]; then
        err "Index or Endpoint not found. Run steps 4 and 5 first."
    fi

    DEPLOYED_ID="periskope_deployed_idx"

    gcloud ai index-endpoints deploy-index "$ENDPOINT_RESOURCE" \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --deployed-index-id="$DEPLOYED_ID" \
        --index="$INDEX_RESOURCE" \
        --display-name="periskope-3072d" \
        --machine-type="$MACHINE_TYPE" \
        --min-replica-count=1 \
        --max-replica-count=1 \
        2>&1 | tee "${EXPORT_DIR}/deploy.log"

    log "Step 6: Deployment initiated (takes 10-20 minutes) ✓"
    log "  ⚠️  This starts billing at ~\$0.094/hr = ~\$68/month"
    log "  Monitor: gcloud ai index-endpoints list --project=$PROJECT_ID --region=$REGION"
}

# ── Status check ──
step_status() {
    log "=== Vector Search Status ==="
    echo ""
    echo "📦 Indexes:"
    gcloud ai indexes list \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --format="table(displayName,name.basename(),updateTime.date(),metadata.config.dimensions)" 2>/dev/null || echo "  (none)"
    echo ""
    echo "🔗 Endpoints:"
    gcloud ai index-endpoints list \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --format="table(displayName,name.basename(),deployedIndexes[0].id)" 2>/dev/null || echo "  (none)"
    echo ""
    echo "📊 Exported data:"
    if [ -f "$EXPORT_FILE" ]; then
        echo "  Vectors: $(wc -l < "$EXPORT_FILE") records"
        echo "  File: $EXPORT_FILE"
    else
        echo "  (not exported yet)"
    fi
}

# ── Main dispatcher ──
main() {
    check_gcloud

    local step="${1:-all}"

    case "$step" in
        1|apis)     step_enable_apis ;;
        2|bucket)   step_create_bucket ;;
        3|export)   step_export_vectors ;;
        4|index)    step_create_index ;;
        5|endpoint) step_create_endpoint ;;
        6|deploy)   step_deploy_index ;;
        status)     step_status ;;
        all)
            step_enable_apis
            step_create_bucket
            step_export_vectors
            step_create_index
            step_create_endpoint
            log ""
            log "=== Steps 1-5 complete ==="
            log "Step 6 (deploy) requires Index to be READY."
            log "Run: bash scripts/vector_search_setup.sh status"
            log "When Index status is READY, run:"
            log "  bash scripts/vector_search_setup.sh 6"
            ;;
        *)
            echo "Usage: $0 {1|2|3|4|5|6|status|all}"
            exit 1
            ;;
    esac
}

main "$@"

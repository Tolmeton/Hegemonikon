#!/usr/bin/env bash
# Pure TPU VM setup for Phase 1 experiments.
# Project and account are pinned on purpose to avoid accidental cross-project use.

set -euo pipefail

PROJECT_ID="${PROJECT_ID:-project-deb07447-0f70-4d65-a91}"
ACCOUNT="${ACCOUNT:-h.raiki.biz@gmail.com}"
TPU_NAME="${TPU_NAME:-sam-cka-run}"

PREFERRED_V5E_TYPE="${PREFERRED_V5E_TYPE:-v5litepod-1}"
PREFERRED_V5E_RUNTIME="${PREFERRED_V5E_RUNTIME:-v2-alpha-tpuv5-lite}"
PREFERRED_V6E_TYPE="${PREFERRED_V6E_TYPE:-v6e-1}"
PREFERRED_V6E_RUNTIME="${PREFERRED_V6E_RUNTIME:-v2-alpha-tpuv6e}"

V5E_ZONES=(
  us-central1-a
  us-south1-a
  us-west1-c
  us-west4-a
)

V6E_ZONES=(
  asia-northeast1-b
  us-central1-b
  us-east1-d
  us-east5-a
  us-east5-b
)

usage() {
  cat <<'EOF'
Usage:
  ./setup_tpu.sh access
  ./setup_tpu.sh enable-api
  ./setup_tpu.sh inventory [v5e|v6e|all]
  ./setup_tpu.sh create <v5e|v6e> <zone>
  ./setup_tpu.sh init <zone>
  ./setup_tpu.sh verify <zone>
  ./setup_tpu.sh full <v5e|v6e> <zone>
  ./setup_tpu.sh cleanup <zone>

Pinned defaults:
  PROJECT_ID=project-deb07447-0f70-4d65-a91
  ACCOUNT=h.raiki.biz@gmail.com
  TPU_NAME=sam-cka-run

Preferred accelerator/runtime pairs:
  v5e -> v5litepod-1 / v2-alpha-tpuv5-lite
  v6e -> v6e-1       / v2-alpha-tpuv6e

Examples:
  ./setup_tpu.sh access
  ./setup_tpu.sh inventory v5e
  ./setup_tpu.sh create v5e us-central1-a
  ./setup_tpu.sh init us-central1-a
  ./setup_tpu.sh verify us-central1-a
  ./setup_tpu.sh full v6e asia-northeast1-b
EOF
}

log() {
  printf '[setup_tpu] %s\n' "$*"
}

die() {
  printf '[setup_tpu] ERROR: %s\n' "$*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

set_account() {
  gcloud config set account "${ACCOUNT}" >/dev/null
}

project_flag() {
  printf -- '--project=%s' "${PROJECT_ID}"
}

zone_flag() {
  local zone="$1"
  printf -- '--zone=%s' "${zone}"
}

family_type() {
  local family="$1"
  case "${family}" in
    v5e) printf '%s' "${PREFERRED_V5E_TYPE}" ;;
    v6e) printf '%s' "${PREFERRED_V6E_TYPE}" ;;
    *) die "Unknown family: ${family}" ;;
  esac
}

family_runtime() {
  local family="$1"
  case "${family}" in
    v5e) printf '%s' "${PREFERRED_V5E_RUNTIME}" ;;
    v6e) printf '%s' "${PREFERRED_V6E_RUNTIME}" ;;
    *) die "Unknown family: ${family}" ;;
  esac
}

family_pattern() {
  local family="$1"
  case "${family}" in
    v5e) printf '^v5litepod-' ;;
    v6e) printf '^v6e-' ;;
    *) die "Unknown family: ${family}" ;;
  esac
}

family_zones() {
  local family="$1"
  case "${family}" in
    v5e) printf '%s\n' "${V5E_ZONES[@]}" ;;
    v6e) printf '%s\n' "${V6E_ZONES[@]}" ;;
    all)
      printf '%s\n' "${V5E_ZONES[@]}"
      printf '%s\n' "${V6E_ZONES[@]}"
      ;;
    *) die "Unknown family: ${family}" ;;
  esac
}

print_access_requirements() {
  cat <<EOF
Required preconditions for ${ACCOUNT} on ${PROJECT_ID}:
  - roles/tpu.admin
  - roles/iam.serviceAccountUser
  - roles/compute.viewer
  - Cloud TPU API enabled: tpu.googleapis.com
  - TPU service identity created if your org policy requires it
EOF
}

check_access() {
  log "Checking account and project access"
  set_account

  if ! gcloud projects describe "${PROJECT_ID}" --format='value(projectId)' >/dev/null 2>&1; then
    print_access_requirements
    die "Cannot access project metadata for ${PROJECT_ID}"
  fi

  if ! gcloud services list --enabled "$(project_flag)" \
      --filter='name:tpu.googleapis.com' \
      --format='value(name)' >/dev/null 2>&1; then
    print_access_requirements
    die "Cannot list enabled services for ${PROJECT_ID}"
  fi

  log "Project access gate passed"
}

enable_api() {
  log "Enabling Cloud TPU API on ${PROJECT_ID}"
  set_account

  gcloud services enable tpu.googleapis.com "$(project_flag)"
  gcloud beta services identity create \
    --service=tpu.googleapis.com \
    "$(project_flag)"
}

list_family_inventory() {
  local family="$1"
  local pattern
  pattern="$(family_pattern "${family}")"

  while IFS= read -r zone; do
    [ -n "${zone}" ] || continue
    log "Inventory ${family} in ${zone}"
    if ! gcloud compute tpus tpu-vm accelerator-types list \
        "$(project_flag)" \
        "$(zone_flag "${zone}")" | awk 'NR>1 {print $1}' | grep -E "${pattern}"; then
      printf '  (none or no permission)\n'
    fi
  done < <(family_zones "${family}")
}

inventory() {
  local target="${1:-all}"
  set_account
  case "${target}" in
    v5e|v6e)
      list_family_inventory "${target}"
      ;;
    all)
      list_family_inventory v5e
      list_family_inventory v6e
      ;;
    *)
      die "inventory expects v5e, v6e, or all"
      ;;
  esac
}

require_preferred_type() {
  local family="$1"
  local zone="$2"
  local expected_type
  expected_type="$(family_type "${family}")"

  log "Checking ${expected_type} in ${zone}"
  if ! gcloud compute tpus tpu-vm accelerator-types list \
      "$(project_flag)" \
      "$(zone_flag "${zone}")" | awk 'NR>1 {print $1}' | grep -Fx "${expected_type}" >/dev/null; then
    log "Available ${family} accelerator types in ${zone}:"
    gcloud compute tpus tpu-vm accelerator-types list \
      "$(project_flag)" \
      "$(zone_flag "${zone}")" | awk 'NR>1 {print $1}' | grep -E "$(family_pattern "${family}")" || true
    die "Preferred type ${expected_type} is not available in ${zone}"
  fi
}

create_tpu() {
  local family="$1"
  local zone="$2"
  local accelerator_type runtime

  accelerator_type="$(family_type "${family}")"
  runtime="$(family_runtime "${family}")"

  set_account
  require_preferred_type "${family}" "${zone}"

  log "Creating TPU VM ${TPU_NAME} in ${zone} (${accelerator_type}, ${runtime})"
  gcloud compute tpus tpu-vm create "${TPU_NAME}" \
    "$(project_flag)" \
    "$(zone_flag "${zone}")" \
    --accelerator-type="${accelerator_type}" \
    --version="${runtime}"
}

remote_script() {
  cat <<'EOF'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
export PJRT_DEVICE=TPU

sudo apt-get update
while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do
  echo "Waiting for dpkg lock..."
  sleep 5
done
sudo apt-get install -y libopenblas-dev

python3 -m pip install --upgrade pip
python3 -m pip install numpy
python3 -m pip install 'torch~=2.5.0' torchvision \
  'torch_xla[tpu]~=2.5.0' \
  -f https://storage.googleapis.com/libtpu-releases/index.html
EOF
}

remote_verify_script() {
  cat <<'EOF'
set -euo pipefail
export PJRT_DEVICE=TPU
python3 - <<'PY'
import torch
import torch_xla.core.xla_model as xm

supported = xm.get_xla_supported_devices("TPU")
print("supported_devices=", supported)
if not supported:
    raise SystemExit("No TPU devices detected")

device = xm.xla_device()
print("xla_device=", device)
t = torch.randn(2, 2, device=device)
print("tensor=", t)
print("verification=ok")
PY
EOF
}

ssh_run() {
  local zone="$1"
  local command="$2"

  gcloud compute tpus tpu-vm ssh "${TPU_NAME}" \
    "$(project_flag)" \
    "$(zone_flag "${zone}")" \
    --command="${command}"
}

init_vm() {
  local zone="$1"
  set_account
  log "Initializing TPU VM ${TPU_NAME} in ${zone}"
  ssh_run "${zone}" "$(remote_script)"
}

verify_vm() {
  local zone="$1"
  set_account
  log "Verifying PyTorch/XLA on TPU VM ${TPU_NAME} in ${zone}"
  ssh_run "${zone}" "$(remote_verify_script)"
}

cleanup_vm() {
  local zone="$1"
  set_account
  log "Deleting TPU VM ${TPU_NAME} in ${zone}"
  gcloud compute tpus tpu-vm delete "${TPU_NAME}" \
    "$(project_flag)" \
    "$(zone_flag "${zone}")" \
    --quiet
}

full_setup() {
  local family="$1"
  local zone="$2"

  check_access
  enable_api
  create_tpu "${family}" "${zone}"
  init_vm "${zone}"
  verify_vm "${zone}"
}

main() {
  require_cmd gcloud
  local cmd="${1:-}"
  case "${cmd}" in
    access)
      check_access
      ;;
    enable-api)
      enable_api
      ;;
    inventory)
      inventory "${2:-all}"
      ;;
    create)
      [ $# -eq 3 ] || die "create requires: <v5e|v6e> <zone>"
      create_tpu "$2" "$3"
      ;;
    init)
      [ $# -eq 2 ] || die "init requires: <zone>"
      init_vm "$2"
      ;;
    verify)
      [ $# -eq 2 ] || die "verify requires: <zone>"
      verify_vm "$2"
      ;;
    full)
      [ $# -eq 3 ] || die "full requires: <v5e|v6e> <zone>"
      full_setup "$2" "$3"
      ;;
    cleanup)
      [ $# -eq 2 ] || die "cleanup requires: <zone>"
      cleanup_vm "$2"
      ;;
    -h|--help|help|"")
      usage
      ;;
    *)
      die "Unknown command: ${cmd}"
      ;;
  esac
}

main "$@"

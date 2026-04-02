#!/bin/bash
# Next.js standalone ビルドに静的アセットをコピーするスクリプト
# next build 後、または systemd ExecStartPre で実行する

set -e

FRONTEND_DIR="/mnt/LinuxHDD/IT-BCP-ITSCM-System/frontend"
STANDALONE_DIR="${FRONTEND_DIR}/.next/standalone/IT-BCP-ITSCM-System/frontend"

if [ ! -d "${STANDALONE_DIR}" ]; then
  echo "ERROR: standalone build not found at ${STANDALONE_DIR}" >&2
  exit 1
fi

# .next/static をコピー
cp -r "${FRONTEND_DIR}/.next/static" "${STANDALONE_DIR}/.next/"
echo "Copied .next/static -> ${STANDALONE_DIR}/.next/static"

# public をコピー
cp -r "${FRONTEND_DIR}/public" "${STANDALONE_DIR}/"
echo "Copied public -> ${STANDALONE_DIR}/public"

echo "Static assets copy complete."

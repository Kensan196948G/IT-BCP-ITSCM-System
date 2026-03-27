#!/bin/bash
# ClaudeOS GitHub Project 状態同期スクリプト
# Usage: ./project-sync.sh <ITEM_ID> <STATUS>
# STATUS: Inbox|Backlog|Ready|Design|Development|Verify|Deploy_Gate|Done|Blocked

set -euo pipefail

ITEM_ID="${1:?Usage: $0 <ITEM_ID> <STATUS>}"
STATUS="${2:?Usage: $0 <ITEM_ID> <STATUS>}"

# GitHub Project設定（初回実行時に取得して設定）
PROJECT_NUMBER="${PROJECT_NUMBER:-1}"
OWNER="${GITHUB_REPOSITORY_OWNER:-Kensan196948G}"
REPO_NAME="IT-BCP-ITSCM-System"

echo "[ClaudeOS] Project状態更新: Item=$ITEM_ID → Status=$STATUS"

# Project IDの取得
PROJECT_ID=$(gh api graphql -f query='
query($owner: String!, $number: Int!) {
  user(login: $owner) {
    projectV2(number: $number) {
      id
      field(name: "Status") {
        ... on ProjectV2SingleSelectField {
          id
          options {
            id
            name
          }
        }
      }
    }
  }
}' -f owner="$OWNER" -F number="$PROJECT_NUMBER" --jq '.data.user.projectV2.id' 2>/dev/null || echo "")

if [ -z "$PROJECT_ID" ]; then
  echo "[ClaudeOS] Warning: Project IDの取得に失敗しました。スキップします。"
  exit 0
fi

# Status Field IDとOption IDの取得
FIELD_DATA=$(gh api graphql -f query='
query($owner: String!, $number: Int!) {
  user(login: $owner) {
    projectV2(number: $number) {
      field(name: "Status") {
        ... on ProjectV2SingleSelectField {
          id
          options {
            id
            name
          }
        }
      }
    }
  }
}' -f owner="$OWNER" -F number="$PROJECT_NUMBER" 2>/dev/null || echo "")

FIELD_ID=$(echo "$FIELD_DATA" | jq -r '.data.user.projectV2.field.id // empty')
OPTION_ID=$(echo "$FIELD_DATA" | jq -r --arg status "$STATUS" '.data.user.projectV2.field.options[] | select(.name == $status) | .id // empty')

if [ -z "$FIELD_ID" ] || [ -z "$OPTION_ID" ]; then
  echo "[ClaudeOS] Warning: Field/Option IDの取得に失敗しました。Status=$STATUS"
  exit 0
fi

# 状態更新
gh api graphql -f query='
mutation($project:ID!, $item:ID!, $field:ID!, $value:String!) {
  updateProjectV2ItemFieldValue(input:{
    projectId: $project
    itemId: $item
    fieldId: $field
    value: { singleSelectOptionId: $value }
  }) {
    projectV2Item { id }
  }
}' -f project="$PROJECT_ID" -f item="$ITEM_ID" -f field="$FIELD_ID" -f value="$OPTION_ID"

echo "[ClaudeOS] Project状態更新完了: $STATUS"

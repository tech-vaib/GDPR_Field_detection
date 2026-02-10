export ATLASSIAN_BASE_URL="https://yourcompany.atlassian.net"
export ATLASSIAN_EMAIL="gdpr-bot@yourcompany.com"
export ATLASSIAN_API_TOKEN="PASTE_TOKEN_HERE"
export JIRA_PROJECT_KEY="GDPR"
export JIRA_ISSUE_TYPE="Task"

curl -X POST \
  -u "gdpr-bot@yourcompany.com:ATLASSIAN_API_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  "https://yourcompany.atlassian.net/rest/api/3/issue" \
  --data '{
    "fields": {
      "project": {
        "key": "GDPR"
      },
      "summary": "[TEST] GDPR CI Mongo CRUD check",
      "description": {
        "type": "doc",
        "version": 1,
        "content": [
          {
            "type": "paragraph",
            "content": [
              {
                "type": "text",
                "text": "This is a test Jira Task created to validate CI/CD integration."
              }
            ]
          }
        ]
      },
      "issuetype": {
        "name": "Task"
      }
    }
  }'


curl -X POST \
  -u "$ATLASSIAN_EMAIL:$ATLASSIAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  "$ATLASSIAN_BASE_URL/rest/api/3/issue" \
  --data '{
    "fields": {
      "project": {
        "key": "'"$JIRA_PROJECT_KEY"'"
      },
      "summary": "[TEST] GDPR CI Mongo CRUD check",
      "description": {
        "type": "doc",
        "version": 1,
        "content": [
          {
            "type": "paragraph",
            "content": [
              {
                "type": "text",
                "text": "This is a test Jira ticket created to validate CI/CD integration."
              }
            ]
          }
        ]
      },
      "issuetype": {
        "name": "'"$JIRA_ISSUE_TYPE"'"
      }
    }
  }'

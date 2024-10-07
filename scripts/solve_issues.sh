#!/bin/bash
set -euo pipefail

# Function to check conditions for automated coding
check_conditions() {
    echo "🔍 Checking conditions for automated coding"

    if [ -n "${CI_MERGE_REQUEST_IID:-}" ]; then
        CHANGED_FILES=$(git diff --name-only HEAD^ HEAD)
        if [ -z "$CHANGED_FILES" ] && [ -n "${CI_MERGE_REQUEST_DESCRIPTION:-}" ]; then
            echo "✅ Conditions met for merge request"
        else
            echo "❌ Conditions not met for merge request"
            exit 0
        fi
    elif [ -n "${GITLAB_ISSUE_ID:-}" ]; then
        ISSUE_DESCRIPTION=$(curl -s --header "PRIVATE-TOKEN: $CODING_AGENT_ACCESS_TOKEN" "https://gitlab.com/api/v4/projects/$CI_PROJECT_ID/issues/$GITLAB_ISSUE_ID" | jq -r '.description')
        if [ -n "$ISSUE_DESCRIPTION" ]; then
            echo "📝 Manual trigger with issue variables: Issue description found"
        else
            echo "❌ Conditions not met: No description in manual trigger issue"
            exit 0
        fi
    elif [ -n "${ISSUE_URL:-}" ] || [ -n "${ISSUE_DESCRIPTION:-}" ]; then
        echo "📝 Manual trigger with issue variables"
    else
        echo "❌ Conditions not met for manual trigger"
        exit 0
    fi
}

# Function to create the data_path markdown file
create_data_path() {
    echo "📄 Creating data_path markdown file"

    DATA_PATH="issue_description.md"
    if [ -n "${ISSUE_URL:-}" ]; then
        DATA_PATH="$ISSUE_URL"
    elif [ -n "${ISSUE_DESCRIPTION:-}" ]; then
        echo "$ISSUE_DESCRIPTION" > "$DATA_PATH"
    elif [ -n "${CI_MERGE_REQUEST_DESCRIPTION:-}" ]; then
        echo "$CI_MERGE_REQUEST_DESCRIPTION" > "$DATA_PATH"
    elif [ -n "${GITLAB_ISSUE_ID:-}" ]; then
        echo "$ISSUE_DESCRIPTION" > "$DATA_PATH"
    fi
}

# Function to determine agent image
determine_agent_image() {
    echo "🔄 Determining agent image based on AGENT variable"

    if [ "${AGENT:-}" = "SWE-crafter" ]; then
        AGENT_IMAGE="umans/swe-crafter"
        AGENT_RUNNER_IMAGE="umans/swe-crafter-run"
        AGENT_GIT_USER="swe-crafter"
        AGENT_GIT_USER_MAIL="swe-crafter@umans.tech"
        CONFIG_FILE="config/test-first_from_url.yaml"
    else
        AGENT_IMAGE="sweagent/swe-agent:latest"
        AGENT_RUNNER_IMAGE="sweagent/swe-agent-run:latest"
        AGENT_GIT_USER="swe-agent"
        AGENT_GIT_USER_MAIL="swe-agent@umans.tech"
        CONFIG_FILE="config/default_from_url.yaml"
    fi
    echo "✅ Selected agent image: $AGENT_IMAGE - Runner image: $AGENT_RUNNER_IMAGE"
}

# Function to pull required Docker images
pull_docker_images() {
    echo "📦 Pulling required Docker images"
    docker pull "$AGENT_RUNNER_IMAGE"
    docker pull "$AGENT_IMAGE"
}

# Function to generate the patch using automated coding tools
generate_patch() {
    echo "⚙️ Generating patch using automated coding tools"

    MODEL_NAME=${MODEL_NAME:-gpt4o}
    REPO_NAME=$(basename "$(pwd)")

    docker run -v /var/run/docker.sock:/var/run/docker.sock \
        -v "$(pwd)":/app/repo/"${REPO_NAME}" \
        -e OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
        -e DEEPSEEK_API_BASE_URL="${DEEPSEEK_API_BASE_URL:-}" \
        -e DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-}" \
        "$AGENT_RUNNER_IMAGE" \
        python run.py --image_name="$AGENT_IMAGE" \
        --model_name "${MODEL_NAME}" \
        --data_path /app/repo/"${REPO_NAME}"/"$DATA_PATH" \
        --repo_path /app/repo/"${REPO_NAME}" --apply_patch_locally \
        --config_file "${CONFIG_FILE}" --skip_existing=False

    rm -f "$DATA_PATH"
}

# Function to commit and push the changes
commit_and_push_changes() {
    echo "🔄 Showing the changes made by applying the generated patch"
    git diff

    echo "📥 Committing the changes"
    git config user.email "${AGENT_GIT_USER_MAIL}"
    git config user.name "${AGENT_GIT_USER}"
    git remote add gitlab_origin "https://oauth2:${CODING_AGENT_ACCESS_TOKEN}@${CI_PROJECT_URL#https://}"
    git add .
    git reset solve_issues.sh

    if [ -n "${CI_MERGE_REQUEST_TITLE:-}" ]; then
        COMMIT_MESSAGE="${CI_MERGE_REQUEST_TITLE} (automated change 🤖✨)"
    else
        COMMIT_MESSAGE="Automated change by ${AGENT} (manual trigger 🤖✨)"
    fi

    git commit -m "$COMMIT_MESSAGE"
    git push gitlab_origin HEAD:"$CI_COMMIT_REF_NAME"
}

# Main function to orchestrate the script execution
main() {
    check_conditions
    create_data_path
    determine_agent_image
    pull_docker_images
    generate_patch
    commit_and_push_changes
}

# Execute the main function
main "$@"

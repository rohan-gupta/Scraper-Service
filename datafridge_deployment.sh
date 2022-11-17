#!/bin/bash

export TZ=Greenwhich/London
now=$(date +"%Y-%m-%dT%TZ")
export COMMITTER_EMAIL="$(git log -1 "$TRAVIS_COMMIT" --pretty="%ce")"
export COMMITTER_NAME="$(git log -1 "$TRAVIS_COMMIT" --pretty="%cn")"
if [ "$TRAVIS_BRANCH" == "develop" ]
then
  environment="staging"
elif [ "$TRAVIS_BRANCH" == "master" ]
then
  environment="production"
fi

if [ "$TRAVIS_BRANCH" == "develop" ] || [ "$TRAVIS_BRANCH" == "master" ]
then
curl -X POST https://ingester.api.thedatafridge.com/v1/deployment-events -H \
"Authorization: Bearer $DATAFRIDGE_API_KEY" -H "Content-Type: application/json" \
-d @- <<EOF
{
  "entity": "Pandora",
  "tribe": "pd-vendor-enablement",
  "timestamp": "$now",
  "initiator": {
    "name": "$COMMITTER_EMAIL",
    "email": "$COMMITER_NAME"
    },
  "product": "vendor-competitive-intelligence",
  "application": "$TRAVIS_REPO_SLUG",
  "environment": "$environment",
  "type": "regular",
  "regions": [
    "$AWS_REGION"
  ],
  "tag": "vci",
  "release_notes": "$TRAVIS_COMMIT_MESSAGE"
}
EOF
fi

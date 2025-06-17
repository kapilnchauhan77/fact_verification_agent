#!/bin/bash
# IAM setup for Vertex AI Agent deployment

# Grant deployed agent access to Secret Manager
gcloud projects add-iam-policy-binding mythic-lattice-455715-q1 \
    --member='serviceAccount:vertex-ai-agent@mythic-lattice-455715-q1.iam.gserviceaccount.com' \
    --role='roles/secretmanager.secretAccessor'

# Grant deployed agent access to Vertex AI
gcloud projects add-iam-policy-binding mythic-lattice-455715-q1 \
    --member='serviceAccount:vertex-ai-agent@mythic-lattice-455715-q1.iam.gserviceaccount.com' \
    --role='roles/aiplatform.user'

# Grant deployed agent access to Cloud Storage (for artifacts)
gcloud projects add-iam-policy-binding mythic-lattice-455715-q1 \
    --member='serviceAccount:vertex-ai-agent@mythic-lattice-455715-q1.iam.gserviceaccount.com' \
    --role='roles/storage.objectAdmin'

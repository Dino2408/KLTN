# Deployment

## Host

Linux host with Docker Engine and Docker Compose v2. Docker Compose is the recommended mechanism for defining and running this multi-container MVP.

Set:
sudo sysctl -w vm.max_map_count=262144

## Bootstrap

cp .env.example .env
bash scripts/bootstrap.sh

## Wazuh

cd deploy/wazuh/single-node
docker compose -f generate-indexer-certs.yml run --rm generator
docker compose up -d

## AI stack

From repository root:
docker compose up -d
docker exec -it ai-siem-ollama ollama pull qwen2.5-coder:7b

## Shuffle

Configure and start the upstream Shuffle deployment under deploy/shuffle.

## First test

Wazuh alert -> AI Gateway -> Ollama -> validated decision -> Shuffle playbook.

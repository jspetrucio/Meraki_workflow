# Docker Distribution - CNL (Cisco Network Language)

Run CNL in a Docker container without installing anything on your host machine.

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
cd docker
docker-compose up -d
```

Access the web UI at: http://localhost:3141

### Option 2: Docker CLI

```bash
# Build the image
docker build -t cnl -f docker/Dockerfile .

# Run the container
docker run -d -p 3141:3141 \
  -v ~/.cnl:/home/cnl/.cnl \
  -v ~/.meraki:/home/cnl/.meraki \
  --name cnl \
  cnl
```

## Volume Mounts Explained

CNL requires two directories to persist credentials and configuration:

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `~/.cnl` | `/home/cnl/.cnl` | CNL configuration and state |
| `~/.meraki` | `/home/cnl/.meraki` | Meraki API credentials |

**Important:** These directories MUST exist on your host machine before starting the container.

```bash
# Create directories if they don't exist
mkdir -p ~/.cnl ~/.meraki
```

## Environment Variables

You can customize CNL's behavior with environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CNL_HOST` | `0.0.0.0` | Server bind address (keep as 0.0.0.0 in container) |
| `CNL_PORT` | `3141` | Server port |
| `CNL_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

**Example with custom variables:**

```bash
docker run -d -p 8080:8080 \
  -v ~/.cnl:/home/cnl/.cnl \
  -v ~/.meraki:/home/cnl/.meraki \
  -e CNL_PORT=8080 \
  -e CNL_LOG_LEVEL=DEBUG \
  --name cnl \
  cnl
```

Or in docker-compose.yml:

```yaml
environment:
  - CNL_HOST=0.0.0.0
  - CNL_PORT=8080
  - CNL_LOG_LEVEL=DEBUG
```

## Container Management

### Start/Stop

```bash
# Start
docker start cnl

# Stop
docker stop cnl

# Restart
docker restart cnl
```

### View Logs

```bash
# Follow logs in real-time
docker logs -f cnl

# Last 100 lines
docker logs --tail 100 cnl
```

### Health Check

CNL includes a built-in health check endpoint:

```bash
# Check container health status
docker inspect --format='{{.State.Health.Status}}' cnl

# Manually test health endpoint
curl http://localhost:3141/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "uptime": 123.45,
  "version": "1.0.0"
}
```

## First-Time Setup

When running CNL for the first time, you need to configure Meraki credentials:

1. Create credentials directory:
   ```bash
   mkdir -p ~/.meraki
   ```

2. Create credentials file:
   ```bash
   cat > ~/.meraki/credentials << 'EOF'
   [default]
   api_key = YOUR_API_KEY_HERE
   org_id = YOUR_ORG_ID_HERE
   EOF
   ```

3. Start the container:
   ```bash
   docker-compose up -d
   ```

4. Access the web UI and run discovery:
   - Open http://localhost:3141
   - Navigate to Discovery
   - Select your organization

## Troubleshooting

### Container won't start

**Check logs:**
```bash
docker logs cnl
```

**Common issues:**
- Port 3141 already in use → change port mapping: `-p 8080:3141`
- Volume mount paths don't exist → create directories with `mkdir -p ~/.cnl ~/.meraki`
- Permissions issues → ensure directories are readable by UID 1000 (cnl user)

### Cannot access web UI

**Verify container is running:**
```bash
docker ps | grep cnl
```

**Check port mapping:**
```bash
docker port cnl
```

**Test from inside container:**
```bash
docker exec -it cnl curl http://localhost:3141/api/v1/health
```

### Credentials not persisted

**Verify volume mounts:**
```bash
docker inspect cnl | grep -A 10 Mounts
```

**Ensure host directories exist:**
```bash
ls -la ~/.cnl ~/.meraki
```

### Image is too large

Expected image size: < 500MB

**Check current size:**
```bash
docker images cnl
```

**Clean up unused layers:**
```bash
docker system prune -a
```

## Building from Source

If you've made changes to CNL and want to rebuild:

```bash
# Rebuild without cache
docker build --no-cache -t cnl -f docker/Dockerfile .

# Or with docker-compose
docker-compose build --no-cache
```

## Security Considerations

- **Non-root user:** Container runs as `cnl` user (UID 1000) for security
- **No secrets in image:** Credentials are NEVER copied into the Docker image
- **Volume mounts:** Credentials are mounted at runtime from host filesystem
- **Health checks:** Built-in monitoring for container orchestration

## Advanced Usage

### Custom networks (multiple services)

If you're running other services (e.g., N8N) in Docker:

```yaml
services:
  cnl:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:
      - "3141:3141"
    volumes:
      - ~/.cnl:/home/cnl/.cnl
      - ~/.meraki:/home/cnl/.meraki
    networks:
      - meraki-network

  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    networks:
      - meraki-network

networks:
  meraki-network:
    driver: bridge
```

### Persistent data volumes

Instead of mounting host directories, use Docker volumes:

```yaml
volumes:
  - cnl-config:/home/cnl/.cnl
  - cnl-credentials:/home/cnl/.meraki

volumes:
  cnl-config:
  cnl-credentials:
```

## Support

- GitHub Issues: https://github.com/josdasil/Meraki_Workflow/issues
- Documentation: https://github.com/josdasil/Meraki_Workflow/blob/main/README.md
- Meraki API Docs: https://developer.cisco.com/meraki/api-v1/

---

**Developed with Claude Code (Opus 4.5)**

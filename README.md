# cloudops-containers

A small Python (FastAPI) service, containerised with Docker. It is the base image for deploying to **Amazon ECS Fargate** and **Kubernetes** later in this project.

| Endpoint | Returns |
|---|---|
| `GET /health` | `{"status": "ok"}`, used by the container health check |
| `GET /` | Service name, version, the container's hostname and the current time |

The hostname shows which container answered a request. This matters once several copies are running behind a load balancer.

## Run locally

Run the tests without Docker first:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```

Build and run the container:

```bash
docker build -t cloudops-containers:0.1.0 .
docker run -d --name cc -p 8000:8000 -e APP_VERSION=0.1.0 cloudops-containers:0.1.0

curl localhost:8000/health
curl localhost:8000/
docker ps            # STATUS shows "(healthy)" after about 30 seconds
docker logs cc
docker exec cc whoami   # appuser, not root

docker rm -f cc      # clean up
```

The image is built as `arm64` on Apple Silicon. That matches ARM64 (Graviton) Fargate tasks, which cost less than x86 tasks.

## Security choices

- **Non-root user.** The app runs as `appuser` (UID 10001), so a compromised process doesn't have root inside the container.
- **Slim base image.** `python:3.12-slim` ships fewer packages, so there's less to patch and a smaller attack surface.
- **Health check.** Docker checks `/health` every 30 seconds, so it reports whether the app actually responds, not just whether the process is alive. ECS and Kubernetes use the same idea.
- **`.dockerignore`.** It keeps git history, virtual environments, tests and local files out of the image.
- **Pinned dependencies with no pip cache.** Builds are repeatable, and the image carries no download cache.
- **Layer caching.** Dependencies are installed before the code is copied in, so a code change doesn't reinstall them.

## Troubleshooting

I broke the container on purpose in three ways to practise diagnosing common faults.

### 1. Wrong port mapping

- **Symptom:** `curl localhost:8000/health` fails with *connection refused*, but `docker ps` shows the container running.
- **Cause:** I ran it with `-p 8000:9000`, which forwards host port 8000 to container port 9000. The app listens on 8000, so nothing answers on 9000.
- **Fix:** Map host port 8000 to the port the app actually listens on: `-p 8000:8000`. To check, `docker ps` shows the mapping, and `EXPOSE` or the app's start command shows the real port.

### 2. App listening only inside the container

- **Symptom:** `curl` from the host fails, but the same request run inside the container with `docker exec` works.
- **Cause:** I started uvicorn with `--host 127.0.0.1`. That makes it listen only on the container's own loopback interface, so traffic forwarded in from outside never reaches it.
- **Fix:** Start the app with `--host 0.0.0.0`, so it listens on all interfaces. On ECS or behind a load balancer, this same mistake makes health checks fail and tasks restart over and over.

### 3. Unhealthy container

- **Symptom:** `docker ps` shows the container as `Up` but `(unhealthy)`.
- **Cause:** I overrode the start command with `sleep 600`. The container is running, but no web server is up, so the `/health` check fails.
- **Fix:** Find out why the check fails with `docker inspect cc --format '{{json .State.Health}}'`, which shows each check's output. Then restore the correct start command. Lesson: a running process doesn't mean a working service.

## What's next

- [ ] Push the image to Amazon ECR with Terraform (scan on push)
- [ ] Deploy to ECS Fargate (ARM64), with 2 tasks behind an Application Load Balancer and logs in CloudWatch
- [ ] GitHub Actions: run tests, build, scan the image with Trivy, and push to ECR using OIDC
- [ ] Run on Kubernetes locally with kind: Deployment, Service, probes and a rolling update

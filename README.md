# Claude Code Discord Agent

A Discord bot that integrates with Claude Code SDK to provide AI-powered responses to user mentions.

## Setup

1. Copy the example configuration:
   ```bash
   cp config.example.yaml config.yaml
   ```

2. Edit `config.yaml` and set your Discord bot token

3. Install dependencies:
   ```bash
   make install
   ```

## Usage

### Local Development
```bash
make run
```

### Docker
```bash
# Build and run with Docker
make build
make docker-run

# Or use Docker Compose
make docker-compose-up
```

## Configuration

The bot is configured via `config.yaml`. Key settings include:
- Discord bot token
- System prompt and personality
- Allowed tools
- Logging configuration

## Development

```bash
make lint    # Run linting
make format  # Format code
make test    # Run tests
```
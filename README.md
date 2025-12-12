# MeshCore Analytics

An integrated Django/GeoDjango web application for monitoring and analyzing MeshCore mesh networks.

**Two complementary features:**
1. **Repeater Monitor** - Real-time health monitoring and telemetry tracking
2. **Signal Mapper** - Field survey tool for signal coverage heatmaps

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full architecture details.

## Quick Start

### Prerequisites

- Python 3.14+
- PostgreSQL with PostGIS extension
- Redis server (for WebSocket channels)
- MeshCore radio connected as USB companionkjjk

### Setup

```bash
# 1. Install dependencies
uv sync

# 2. Create database
createdb maxdb
psql maxdb -c "CREATE EXTENSION postgis;"

# 3. Create .env file
cp .env.example .env

# 4. Run migrations
uv run manage.py migrate

# 5. Set up your USB Companion
uv run python manage.py find_usb_radio --save

# 6. Start server
uv run daphne -b 0.0.0.0 -p 8000 max.asgi:application
```

**Browser:**
- Mesh Home: http://localhost:8000/
- Admin: http://localhost:8000/admin/
- API: http://localhost:8000/api/v1/


## Development Commands

```bash
# Run with Channels/WebSocket support (REQUIRED for Signal Mapper)
uv run daphne -b 0.0.0.0 -p 8000 max.asgi:application

# Find connected USB radios
uv run python manage.py find_usb_radio
uv run python manage.py find_usb_radio --save

# Load contacts from USB radio
uv run python manage.py load_radio_data

# Run migrations
uv run python manage.py migrate

# Create superuser
uv run python manage.py createsuperuser

# Run tests
uv run python manage.py test --parallel auto

# Manage dependencies
uv pip list --outdated
uv lock --upgrade
uv sync
```

## Project Structure

```
├── max/                    # Main Django app
│   ├── models.py           # Node, SignalMeasurement, RepeaterStats
│   ├── consumers.py        # WebSocket consumer (GPS/signal)
│   ├── radio_interface.py  # USB radio interface
│   ├── static/max/js/
│   │   ├── pi-connection.js       # WebSocket client
│   │   ├── measurement-collector.js
│   │   ├── heatmap-renderer.js
│   │   └── signal-mapper.js
│   └── templates/
├── api/                    # REST API
├── docs/
│   └── ARCHITECTURE.md     # Full system docs
└── pyproject.toml
```

## API Endpoints

- `GET /api/v1/nodes/` - List active nodes
- `GET/POST /api/v1/measurements/` - Signal measurements
- `WS /ws/signal/` - WebSocket for GPS/signal streaming


## Related Projects

### MeshCore MQTT Broker
**Repository:** https://github.com/michaelhart/meshcore-mqtt-broker

**Important Note:** The main developer (Tree) runs the main meshcore-analyzer website. This MQTT broker project may have overlapping functionality with our analytics platform. We should coordinate with them as there may be opportunities to merge or integrate our projects in the future.

## Next Steps

- [ ] Fine-tune MeshCore radio API integration 
- [ ] Build Repeater Monitor frontend dashboard
- [ ] Deploy to Raspberry Pi with systemd services
- [ ] Add advanced heatmap interpolation
- [ ] Evaluate integration opportunities with meshcore-mqtt-broker

See full roadmap in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

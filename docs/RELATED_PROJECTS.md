# Related MeshCore Projects

## MeshCore MQTT Broker
**Repository:** https://github.com/michaelhart/meshcore-mqtt-broker

The main developer (Tree) runs the main meshcore-analyzer website. This MQTT broker project may have overlapping functionality with our platform. We should coordinate with them as there may be opportunities to merge or integrate our projects in the future.

## Mesh Map
**Repository:** https://github.com/kallanreed/mesh-map
**Live Demo:** https://mesh-map.pages.dev/

Built with JavaScript and deployed on Cloudflare's serverless infrastructure, it provides tools for visualizing signal coverage patterns, managing repeater locations, and wardriving data collection. The application helps network administrators track and analyze mesh network coverage across geographical areas using MQTT message data.

## Official MeshCore Maps

### MeshCore Node Map
**URL:** https://map.meshcore.dev/
**Repository:** https://github.com/recrof/map.meshcore.dev

The official MeshCore map - a fully static site that uses a backend API deployed at meshcore.dev/api/v1/nodes. Provides real-time visualization of all MeshCore nodes on the network.

### MeshCore Map (UK)
**URL:** https://meshcore.co.uk/map.html

Another official MeshCore map page for viewing network nodes and coverage.

### RO-Mesh MeshCore Map
**Repository:** https://github.com/RO-mesh/meshcore-map/

Listed as an "Official MeshCore Map" implementation.

## Other Mapping and Visualization Tools

### MeshExplorer
**Repository:** https://github.com/ajvpot/meshexplorer

A comprehensive real-time map, chat client, and packet analysis tool for MeshCore and Meshtastic networks. Features include:
- Real-time visualization of mesh nodes on an interactive map
- Built-in chat client for network communication
- Packet analysis and statistical tracking
- Message tracking and monitoring

### Mesh Coverage Map
**Repository:** https://github.com/lane83/mesh-coverage-map

A dedicated visualization tool specifically designed for mesh network coverage data analysis.

## Key Features Across Projects

Many of these tools support **Trace Path Map mode**, which allows users to:
- Click on nodes in a specific order to visualize routing paths
- Test new repeater placements
- Understand how terrain and node spacing affect coverage
- See numbered overlays showing the route progression

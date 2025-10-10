#!/usr/bin/env python3
# File path: ~/code/ltphongssvn/ac215e115groupproject/reconstruct_docker_compose.py
# This script reconstructs docker-compose.yml from running container metadata

import json
import yaml
import sys
from pathlib import Path

def extract_service_config(container):
    """Extract Docker Compose service configuration from container metadata"""
    
    # Get basic service info
    service_name = container['Config']['Labels']['com.docker.compose.service']
    config = container['Config']
    host_config = container['HostConfig']
    
    # Build service configuration
    service = {
        'image': config['Image'],
        'container_name': container['Name'].lstrip('/')
    }
    
    # Extract environment variables (filter out system ones)
    env_vars = {}
    system_vars = ['PATH', 'GOSU_VERSION', 'LANG', 'PG_MAJOR', 'PG_VERSION', 
                   'PG_SHA256', 'DOCKER_PG_LLVM_DEPS', 'PGDATA']
    for env in config.get('Env', []):
        if '=' in env:
            key, value = env.split('=', 1)
            if key not in system_vars:
                env_vars[key] = value
    if env_vars:
        service['environment'] = env_vars
    
    # Extract port mappings
    if host_config.get('PortBindings'):
        ports = []
        for container_port, bindings in host_config['PortBindings'].items():
            for binding in bindings:
                host_port = binding['HostPort']
                ports.append(f"{host_port}:{container_port.replace('/tcp', '')}")
        if ports:
            service['ports'] = ports
    
    # Extract volumes
    volumes = []
    for mount in container.get('Mounts', []):
        if mount['Type'] == 'bind':
            # Convert Windows path to WSL path
            source = mount['Source'].replace('\\\\wsl.localhost\\Ubuntu\\home', '/home')
            source = source.replace('\\', '/')
            volumes.append(f".{source.split('ac215e115groupproject')[1]}:{mount['Destination']}:{'ro' if mount.get('Mode') == 'ro' else 'rw'}")
        elif mount['Type'] == 'volume':
            # Use volume name without project prefix
            volume_name = mount['Name'].replace('ac215e115groupproject_', '')
            volumes.append(f"{volume_name}:{mount['Destination']}")
    if volumes:
        service['volumes'] = volumes
    
    # Extract command if present
    if config.get('Cmd') and config['Cmd'] != [] and 'postgres' in service_name:
        # Special handling for postgres command
        service['command'] = ' '.join(config['Cmd'])
    
    # Extract healthcheck
    if config.get('Healthcheck'):
        hc = config['Healthcheck']
        if hc.get('Test'):
            healthcheck = {
                'test': hc['Test'],
                'interval': f"{hc.get('Interval', 10000000000) // 1000000000}s",
                'timeout': f"{hc.get('Timeout', 5000000000) // 1000000000}s",
                'retries': hc.get('Retries', 5)
            }
            service['healthcheck'] = healthcheck
    
    # Add restart policy
    if host_config.get('RestartPolicy', {}).get('Name'):
        service['restart'] = host_config['RestartPolicy']['Name']
    
    # Add networks
    service['networks'] = ['rice_market_network']
    
    return service_name, service

def main():
    # Load container configurations
    with open('running_containers_config.json', 'r') as f:
        containers = json.load(f)
    
    # Build docker-compose structure
    compose = {
        'version': '3.8',
        'services': {},
        'networks': {
            'rice_market_network': {
                'driver': 'bridge'
            }
        },
        'volumes': {}
    }
    
    # Process each container
    for container in containers:
        service_name, service_config = extract_service_config(container)
        compose['services'][service_name] = service_config
        
        # Track named volumes
        for mount in container.get('Mounts', []):
            if mount['Type'] == 'volume':
                volume_name = mount['Name'].replace('ac215e115groupproject_', '')
                compose['volumes'][volume_name] = {'driver': 'local'}
    
    # Write docker-compose.yml
    with open('docker-compose-reconstructed.yml', 'w') as f:
        yaml.dump(compose, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    print("Docker Compose file reconstructed successfully!")
    print("Created: docker-compose-reconstructed.yml")
    print(f"Services found: {', '.join(compose['services'].keys())}")
    print(f"Named volumes: {', '.join(compose['volumes'].keys())}")

if __name__ == '__main__':
    main()

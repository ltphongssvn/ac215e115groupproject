#!/usr/bin/env python3
# File path: ~/code/ltphongssvn/ac215e115groupproject/create_final_docker_compose.py
# This script creates the final docker-compose.yml with proper formatting and comments
# It includes safety features like automatic backup before overwriting

import yaml
import json
import shutil
from datetime import datetime
from pathlib import Path

def create_docker_compose():
    """Create a properly formatted docker-compose.yml with comments"""
    
    # First, create a backup of the existing docker-compose.yml if it exists
    docker_compose_path = Path('docker-compose.yml')
    if docker_compose_path.exists():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'docker-compose.yml.backup.{timestamp}'
        shutil.copy2('docker-compose.yml', backup_name)
        print(f"Created backup: {backup_name}")
        print(f"Backup size: {Path(backup_name).stat().st_size} bytes")
    else:
        print("No existing docker-compose.yml found, creating new file")
    
    # Read the reconstructed configuration to verify it exists
    reconstructed_path = Path('docker-compose-reconstructed.yml')
    if not reconstructed_path.exists():
        print("ERROR: docker-compose-reconstructed.yml not found!")
        print("Please run reconstruct_docker_compose.py first")
        return False
    
    with open('docker-compose-reconstructed.yml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Create the final docker-compose.yml with proper formatting
    compose_content = '''# File path: ~/code/ltphongssvn/ac215e115groupproject/docker-compose.yml
# Docker Compose configuration for Rice Market AI System local development
# This setup provides a complete development environment with PostgreSQL, Redis, and admin tools

version: '3.8'

services:
  # PostgreSQL database - Primary data store for the Rice Market application
  postgres:
    image: postgres:15-alpine
    container_name: rice_market_postgres
    environment:
      # Database credentials - Using simple password for local dev only
      POSTGRES_USER: rice_admin
      POSTGRES_PASSWORD: localdev123
      POSTGRES_DB: rice_market_db
      
      # PostgreSQL initialization settings
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=en_US.utf8"
      
      # Performance tuning matching production settings
      POSTGRES_MAX_CONNECTIONS: 100
      POSTGRES_SHARED_BUFFERS: 256MB
    
    ports:
      - "5433:5432"  # Exposed on 5433 to avoid conflicts with local PostgreSQL
    
    volumes:
      # Mount initialization SQL script as read-only
      - ./data-pipeline/schema/postgresql_ddl.sql:/docker-entrypoint-initdb.d/01_schema.sql:ro
      # Persistent data storage
      - postgres_data:/var/lib/postgresql/data
    
    # Enable query performance monitoring and detailed logging for development
    command: >
      postgres
      -c shared_preload_libraries=pg_stat_statements
      -c pg_stat_statements.track=all
      -c log_statement=all
      -c log_duration=on
    
    # Health check ensures database is ready before dependent services start
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U rice_admin -d rice_market_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    
    networks:
      - rice_market_network

  # Redis cache and session store - Provides high-speed data access
  redis:
    image: redis:7-alpine
    container_name: rice_market_redis
    ports:
      - "6380:6379"  # Exposed on 6380 to avoid conflicts with local Redis
    
    volumes:
      - redis_data:/data  # Persistent storage for Redis snapshots
    
    # Health check ensures Redis is responsive
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    
    networks:
      - rice_market_network

  # pgAdmin - Web-based PostgreSQL management interface
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: rice_market_pgadmin
    environment:
      # pgAdmin configuration for local development
      PGADMIN_DEFAULT_EMAIL: admin@example.com
      PGADMIN_DEFAULT_PASSWORD: admin123
      PGADMIN_CONFIG_SERVER_MODE: 'False'  # Desktop mode for single user
      PGADMIN_CONFIG_MASTER_PASSWORD_REQUIRED: 'False'  # Simplified for dev
    
    ports:
      - "5050:80"  # Access pgAdmin at http://localhost:5050
    
    volumes:
      - pgadmin_data:/var/lib/pgadmin  # Persist pgAdmin configuration
    
    networks:
      - rice_market_network

  # Adminer - Lightweight database management interface
  adminer:
    image: adminer:latest
    container_name: rice_market_adminer
    environment:
      ADMINER_DEFAULT_SERVER: postgres  # Auto-connect to postgres service
      ADMINER_DESIGN: pepa-linha  # Modern UI theme
    
    ports:
      - "8081:8080"  # Access Adminer at http://localhost:8081
    
    networks:
      - rice_market_network

# Named volumes for data persistence
volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  pgadmin_data:
    driver: local

# Custom network for service communication
networks:
  rice_market_network:
    driver: bridge
    # The bridge driver creates an isolated network where services
    # can communicate using their service names as hostnames
'''
    
    # Write the final docker-compose.yml
    with open('docker-compose.yml', 'w') as f:
        f.write(compose_content)
    
    print("\nSuccessfully created docker-compose.yml")
    print(f"New file size: {Path('docker-compose.yml').stat().st_size} bytes")
    print("\nService endpoints:")
    print("  PostgreSQL: localhost:5433 (user: rice_admin, password: localdev123)")
    print("  Redis:      localhost:6380")
    print("  pgAdmin:    http://localhost:5050 (admin@example.com / admin123)")
    print("  Adminer:    http://localhost:8081 (server: postgres, user: rice_admin)")
    print("\nThe file has been created with helpful comments explaining each section.")
    print("\nTo verify the configuration matches your running containers:")
    print("  docker compose config --quiet && echo 'Configuration is valid'")
    return True

if __name__ == '__main__':
    success = create_docker_compose()
    if not success:
        exit(1)

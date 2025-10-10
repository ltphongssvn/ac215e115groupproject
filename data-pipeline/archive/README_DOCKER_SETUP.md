# File path: ~/code/ltphongssvn/ac215e115groupproject/README_DOCKER_SETUP.md
# Rice Market AI System - Docker Development Environment Setup Guide

## Overview

This guide walks you through setting up a local development environment for the Rice Market AI System using Docker Compose. The system consists of a Vietnamese rice trading database with PostgreSQL as the primary datastore, Redis for caching, and web-based database management tools. The setup demonstrates enterprise-grade practices for handling sensitive credentials and maintaining data security.

## System Architecture

The Docker Compose environment creates four interconnected services that simulate our production architecture:

**PostgreSQL 15 Alpine** serves as our primary database, storing 13,638 records across eight core tables that capture rice market operations including customers, commodities, contracts, shipments, and inventory movements. The database schema reflects Vietnamese business operations with fields for warehouse locations (BX - Bãi Xếp), shift timings, and quality metrics.

**Redis 7 Alpine** provides high-speed caching for frequently accessed data and session management. This improves application performance by reducing database load for repetitive queries.

**pgAdmin 4** offers a comprehensive web interface for database administration, allowing you to visually explore table structures, run queries, and monitor database performance.

**Adminer** provides a lightweight alternative database interface that's particularly useful for quick data inspections and simple query execution.

## Prerequisites

Before beginning setup, ensure you have the following installed on your development machine:

**Docker Desktop** (version 20.10 or higher) with Docker Compose support. Docker Desktop includes both Docker Engine and Docker Compose, providing everything needed to run containerized applications. You can download it from https://www.docker.com/products/docker-desktop/

**Python 3.9 or higher** if you plan to run the Airtable synchronization scripts. The scripts use modern Python features and require recent versions for proper functionality.

**Git** for cloning the repository and managing version control. This is essential for collaborating with the team and tracking changes.

**A text editor** suitable for editing configuration files. Visual Studio Code, Sublime Text, or even nano/vim will work perfectly.

## Initial Setup Steps

### Step 1: Clone the Repository

First, clone the repository and navigate to the project directory. If you're a team member, you likely already have access. If you're a reviewer, please request access from the team lead.

```bash
git clone [repository-url]
cd ac215e115groupproject
git checkout feature/airtable-to-cloudsql-pipeline_nan_oct_02_06_54am
```

### Step 2: Understanding the Docker Compose Configuration

Examine the `docker-compose.yml` file to understand the services being created. This file defines our entire local infrastructure as code. Each service specification includes the Docker image to use, environment variables for configuration, port mappings for external access, volume mounts for data persistence, and health checks for monitoring service readiness.

The PostgreSQL service, for example, runs on port 5433 (instead of the default 5432) to avoid conflicts with any PostgreSQL installation you might have on your local machine. This is a common practice when running multiple database instances.

### Step 3: Setting Up the Database Schema

The PostgreSQL container automatically initializes the database schema from the file `data-pipeline/schema/postgresql_ddl.sql`. This file contains all table definitions, indexes, and relationships needed for the rice market database. The schema includes specialized fields for Vietnamese rice trading operations such as moisture percentage tracking, warehouse location codes, and shift-based production metrics.

Verify this file exists by running:
```bash
ls -la data-pipeline/schema/postgresql_ddl.sql
```

If the file doesn't exist, the PostgreSQL container will start but won't have any tables, making the system non-functional. Contact the team lead if this file is missing.

### Step 4: Starting the Docker Environment

Launch all services using Docker Compose. The first run will download all necessary Docker images, which may take several minutes depending on your internet connection:

```bash
docker compose up -d
```

The `-d` flag runs the containers in detached mode, meaning they run in the background and don't tie up your terminal. This is preferred for development work since you'll want to use your terminal for other commands.

Monitor the startup process to ensure all services initialize correctly:
```bash
docker compose ps
docker compose logs -f postgres
```

The PostgreSQL service should show "database system is ready to accept connections" when fully initialized. Redis should show "Ready to accept connections". Press Ctrl+C to stop following the logs once you see these messages.

## Configuring Airtable Synchronization (Optional)

The database can be populated with data from Airtable using our synchronization scripts. This step requires access to the Airtable API, which involves sensitive credentials that must be handled securely.

### Understanding Credential Security

API keys are like passwords that grant access to external services. They should never be committed to version control because Git maintains a permanent history of all files, meaning once a credential is committed, it's compromised forever. Even in private repositories, credentials can be exposed through repository forks, developer machine compromises, or accidental repository publicity.

Instead, we use environment variables to inject credentials at runtime. This separation of configuration from code is one of the twelve factors of modern application development (https://12factor.net/config) and represents an industry best practice.

### Setting Up Your Environment File

First, copy the environment template file to create your local configuration:

```bash
cp data-pipeline/.env.example data-pipeline/.env
```

The `.env` file is listed in `.gitignore`, ensuring it won't accidentally be committed to the repository. This is a critical safety mechanism that prevents credential exposure.

### Obtaining the Airtable API Key

For team members, the Airtable API key is available through our secure credential sharing system. Please contact the team lead who will provide the key through one of these secure channels:

- Encrypted email using PGP or S/MIME
- Team password manager (if your organization uses one)
- Secure messaging platform with end-to-end encryption
- In-person or voice communication for highest security

For code reviewers, we cannot provide production API keys for security reasons. However, you can:
1. Use the Docker environment without synchronization to review the database structure
2. Request a demonstration during code review sessions
3. Create your own Airtable base with sample data for testing

### Configuring the Environment File

Edit the `.env` file with your preferred text editor and add the actual credentials:

```bash
# Edit the file (using nano as an example)
nano data-pipeline/.env

# Add your actual API key in place of the placeholder
AIRTABLE_API_KEY=pat[your-actual-key-here]
AIRTABLE_BASE_ID=appmeTyHLozoqighD
```

Save the file and verify it's properly configured by running the connection test:

```bash
python data-pipeline/test_connections.py
```

You should see successful connections for both Airtable and PostgreSQL. If Airtable connection fails, verify your API key is correct and has access to the specified base.

### Running the Initial Data Synchronization

Once credentials are configured, run the initial synchronization to populate your database:

```bash
# For first-time setup, run a full synchronization
SYNC_MODE=full python data-pipeline/sync_consolidated_singlefile.py

# For subsequent updates, use incremental mode
python data-pipeline/sync_consolidated_singlefile.py
```

The full synchronization will fetch all 13,638 records from eight Airtable tables and insert them into PostgreSQL. This process typically takes 2-3 minutes depending on network speed and Airtable API rate limits. The script respects Airtable's rate limiting (5 requests per second) to avoid API throttling.

## Accessing the Services

Once the environment is running, you can access the services through your web browser:

### PostgreSQL Database
- **Connection String**: `postgresql://rice_admin:localdev123@localhost:5433/rice_market_db`
- **Host**: localhost
- **Port**: 5433 (note: not the default 5432)
- **Database**: rice_market_db
- **Username**: rice_admin
- **Password**: localdev123

### Redis Cache
- **Connection String**: `redis://localhost:6380`
- **Host**: localhost
- **Port**: 6380 (note: not the default 6379)
- **No authentication required for local development**

### pgAdmin Web Interface
- **URL**: http://localhost:5050
- **Email**: admin@example.com
- **Password**: admin123
- **Note**: You'll need to add the PostgreSQL server manually on first use:
    - Right-click "Servers" → "Create" → "Server"
    - Name: Rice Market Local
    - Connection Host: postgres (the Docker service name)
    - Port: 5432 (internal port, not 5433)
    - Username: rice_admin
    - Password: localdev123

### Adminer Interface
- **URL**: http://localhost:8081
- **System**: PostgreSQL
- **Server**: postgres (the Docker service name)
- **Username**: rice_admin
- **Password**: localdev123
- **Database**: rice_market_db

## Understanding the Database Structure

The database contains eight primary tables representing a Vietnamese rice trading operation:

**customers** (105 records) stores business relationships with buyers and suppliers. Each customer record includes company details, contact information, and relationship metadata.

**commodities** (45 records) tracks different rice varieties and grades. This includes various rice types from different regions, with quality specifications and processing requirements.

**price_lists** (5 records) defines pricing structures for different market conditions and customer segments. These link commodities to their prices under specific conditions.

**contracts_hp_ng** and **contracts_hp_ng___2** (3,248 records total) document legal agreements for rice trades. The "hp_ng" suffix is an abbreviation of "hợp đồng" (Vietnamese for contract). These tables track contract terms, quantities, prices, and delivery schedules.

**shipments** (383 records) monitors the physical movement of rice from warehouses to customers. Each shipment links to contracts and tracks delivery status, quantities, and logistics information.

**inventory_movements** (8,342 records) provides detailed tracking of rice flow through warehouses. The "BX" prefixed columns represent different warehouse locations (Bãi Xếp - storage yards), with names like "BX Á Châu" (Asia warehouse) indicating geographical or functional divisions.

**finished_goods** (1,690 records) tracks production output across different shifts. Field names include shift timings like "n_16h30_19h" (evening shift 4:30 PM - 7:00 PM) and production metrics "theo đầu bao" (per bag header).

## Troubleshooting Common Issues

### Port Conflicts

If you encounter errors about ports already being in use, you likely have local services running on the same ports. You can either stop the conflicting services or modify the port mappings in docker-compose.yml. For example, if PostgreSQL is already running locally on 5433, you could change the mapping to `"15433:5432"` to use port 15433 instead.

### Database Not Initializing

If tables aren't created when PostgreSQL starts, verify that the schema file exists and is properly mounted. Check the PostgreSQL logs for any SQL errors during initialization:
```bash
docker compose logs postgres | grep ERROR
```

### Airtable Sync Failures

Common causes include incorrect API keys (verify the key starts with 'pat' and has the correct length), rate limiting (the script handles this automatically, but extreme cases may require waiting), network connectivity issues (check your internet connection and firewall settings), and incorrect base ID (verify you're using the right Airtable base).

### Container Health Checks Failing

If containers show as unhealthy, examine their logs to identify the issue:
```bash
docker compose ps  # Check status
docker compose logs [service_name]  # View detailed logs
docker exec rice_market_postgres pg_isready -U rice_admin  # Test PostgreSQL directly
docker exec rice_market_redis redis-cli ping  # Test Redis directly
```

## Stopping and Cleaning Up

To stop all services while preserving data:
```bash
docker compose down
```

To completely remove all containers, networks, and volumes (WARNING: this deletes all data):
```bash
docker compose down -v
```

To remove only containers and networks but preserve data volumes:
```bash
docker compose down
docker volume ls  # Lists all volumes
# Data is preserved in volumes with names like:
# ac215e115groupproject_postgres_data
# ac215e115groupproject_redis_data
# ac215e115groupproject_pgadmin_data
```

## Security Best Practices

This project demonstrates several important security practices that should be followed in all development work:

**Never commit credentials to version control.** Use environment variables and .env files that are gitignored. This prevents credentials from entering Git history where they become permanent and irretrievable.

**Use different credentials for different environments.** Local development should use simple passwords (like 'localdev123'), while production uses strong, randomly generated credentials stored in secure vaults.

**Rotate credentials regularly.** If a credential is ever exposed (even accidentally), revoke it immediately and generate a new one. This limits the window of vulnerability.

**Apply the principle of least privilege.** Each service and user should have only the minimum permissions necessary to function. Our PostgreSQL user, for example, has access only to the rice_market_db database.

**Document security practices clearly.** This README serves as an example of how to guide users through secure setup without exposing sensitive information.

## Additional Resources

For deeper understanding of the technologies used:

- Docker Compose documentation: https://docs.docker.com/compose/
- PostgreSQL documentation: https://www.postgresql.org/docs/15/
- Redis documentation: https://redis.io/documentation
- Airtable API documentation: https://airtable.com/developers/web/api/introduction
- Twelve-Factor App methodology: https://12factor.net/

## Support

For team members experiencing issues:
1. Check this troubleshooting guide first
2. Review the docker compose logs for error messages
3. Contact the team lead with specific error messages and steps to reproduce

For code reviewers:
1. The Docker environment can be reviewed without Airtable credentials
2. Focus on the docker-compose.yml structure and schema definitions
3. Request a demonstration if you need to see the synchronization in action

Remember that this is a development environment optimized for ease of use and debugging. Production deployments would include additional security hardening, monitoring, and high availability configurations.

## Contributing

When contributing to this project, maintain the security practices outlined above. Never commit real credentials, always use environment variables for configuration, document any new services or configuration clearly, and update this README when adding new setup requirements.

This project represents real-world enterprise practices adapted for educational purposes. The patterns and practices demonstrated here are directly applicable to professional software development environments.



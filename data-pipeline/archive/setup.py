from setuptools import setup, find_packages

setup(
    name="rice-market-pipeline",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "psycopg2-binary>=2.9.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "pytz>=2024.1",
    ],
    python_requires=">=3.11",
    author="Rice Market Data Team",
    description="AirTable to PostgreSQL synchronization for rice market operations",
)

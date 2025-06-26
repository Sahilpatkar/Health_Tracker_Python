# Health_Tracker_Python
Project to track and monitor daily food and exercise habits and monitor progress

## Configuration

Before running the application you need two configuration files:

1. **`.env`** – stores API keys used by the Streamlit app.
2. **`.streamlit/secrets.toml`** – holds database credentials for the Docker
   MySQL service.

### Example `.env`

```bash
GROQ_API_KEY=your_groq_api_key
LANGCHAIN_API_KEY=your_langchain_api_key
```

### Example `.streamlit/secrets.toml`

```toml
[database_docker]
host = "mysql"     # container name from docker-compose
port = 3306
user = "user"
password = "123456"
database = "healthtracker"
```

## Running with Docker

The project requires **Docker** and **docker-compose** to be installed. Build
the image and start all services with the following commands:

```bash
docker build -t health_tracker .
docker-compose up
```

The Streamlit interface will be available on
`http://localhost:8501` and MySQL will listen on port `3306`.  Kafka
components are exposed on ports `9092`, `9093`, `8080` and `8082` as configured
in `docker-compose.yml`.

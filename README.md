# Backend FastAPI Sensors

![License](https://img.shields.io/badge/license-MIT-blue)

This is a FastAPI project for managing sensor data, built with Python 3.11, FastAPI, SQLAlchemy, and PostgreSQL. The project uses Poetry for dependency management and task automation.

### ⚠️ Attention
### This project is part of frontend project [frontend-fastapi-sensors](https://github.com/johanguse/frontend-fastapi-sensors).


### 🔐 Autorization

Current we have three users on database, choose one of them to create a token:
```
username: johanguse@gmail.com
password: mE8eAazZ28xmmHG$
```
```
username: jane.smith@example.com
password: mE8eAazZ28xmmHG$
```
```
username: alice.johnson@example.com
password: mE8eAazZ28xmmHG$
```


### Things could be improve with extra time aka to-do list.

 - Improve the documentation
 - Improve CI/CD pipeline. Use github action to run the tests before push live
 - Add more tests
 - Add more endpoints to user like reset password, change password, etc.
 - Add more endpoints to company like add sensors, etc.
 - Add more endpoints to sensor like add data, etc.


## 🤖 Tech Stack

- **Python 3.11**: The core programming language used for the backend.
- **[FastAPI](https://fastapi.tiangolo.com/)**: A modern, fast (high-performance) web framework for building APIs with Python 3.6+ based on standard Python type hints.
- **[SQLAlchemy](https://www.sqlalchemy.org/)**: The Python SQL toolkit and Object-Relational Mapping (ORM) library.
- **[PostgreSQL](https://www.postgresql.org/)**: A powerful, open-source object-relational database system.
- **[Pydantic](https://pydantic-docs.helpmanual.io/)**: Data validation and settings management using Python type annotations.
- **[Alembic](https://alembic.sqlalchemy.org/)**: A lightweight database migration tool for SQLAlchemy.
- **[Poetry](https://python-poetry.org/)**: Python dependency management and packaging made easy.
- **[pytest](https://docs.pytest.org/)**: A framework that makes it easy to write small tests, yet scales to support complex functional testing.
- **[Ruff](https://github.com/astral-sh/ruff)**: An extremely fast Python linter and code formatter, written in Rust.

## ⚒️ Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11**: You can download it from [python.org](https://www.python.org/downloads/).
- **Poetry**: Install it by following the instructions on the [official Poetry website](https://python-poetry.org/docs/#installation).
- **PostgreSQL**: Install and set up PostgreSQL on your system. You can download it from [postgresql.org](https://www.postgresql.org/download/).
- **Docker** (optional): If you prefer to run the project using Docker, make sure you have [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install/) installed.

## 🚀 Installation and Running Instructions

### Using Poetry

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/backend-fastapi-sensors.git
   cd backend-fastapi-sensors
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Set up your environment variables by copying the `.env.example` file to `.env` and filling in the required values.

4. Run database migrations:
   ```bash
   poetry run alembic upgrade head
   ```

5. Start the FastAPI server:
    ```bash
   task run
   ```
   or

   ```bash
   poetry run uvicorn app.main:app --reload
   ```

The API will be available at `http://127.0.0.1:8000/`.
And the API documentation will be available at `http://127.0.0.1:8000/docs`.

### Using Docker

1. Clone the repository as described above.

2. Build and run the Docker containers:
   ```bash
   docker-compose up --build
   ```

This will start both the FastAPI application and the PostgreSQL database. The API will be available at `http://localhost:8000`.

## 🧪 Running Tests

To run the test suite:

```bash
poetry run task test
```

This command will run the linter first, then execute the tests using pytest, and finally run the tests with coverage.

## 📝 Extra: Linting and Formatting

To run the linter:

```bash
poetry run task lint
```

To format the code:

```bash
poetry run task format
```

## Available Tasks

The following tasks are defined in the `pyproject.toml` file and can be run using `poetry run task <taskname>`:

- `lint`: Run the linter (ruff) on the project
- `format`: Format the code using ruff
- `run`: Start the FastAPI development server
- `pre_test`: Run the linter before running tests
- `test`: Run the tests with pytest
- `post_test`: Run the tests with coverage

## Deployment

This project can be easily deployed on [Render](https://render.com/).

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/render-examples/fastapi)

## Database diagram (schema)

![image](https://github.com/user-attachments/assets/a8fb5fe4-d59e-4342-a549-bac3cc51d726)


## License

This project is licensed under the MIT License.

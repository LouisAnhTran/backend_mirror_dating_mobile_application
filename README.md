## Getting started

### 1. Install Softwares:

Install the following tools and softwares to your local machine:

1. Database management system:
   
+ [PostgreSQL](https://www.postgresql.org/download/)

2. GUI Administration and management tool for PostgreSQL

+ [PgAdmin4](https://www.postgresql.org/download/)

3. Python dependencies and packages managements:

+ [Poetry](https://python-poetry.org/docs/)

4. [Optional] Work with AWS Services from CLI:

+ [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html)


### 2. Run Backend:
Run the following commands to spin up backend

+ Install the dependencies listed in the pyproject.toml file and lock them in the poetry.lock file into your virtual environment.

```
poetry install
```

+  create and activate a virtual environment

```
poetry shell
```

+ run the app

```
poetry run python main.py
```

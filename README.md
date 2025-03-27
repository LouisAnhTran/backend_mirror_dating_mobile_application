## Getting started

### 1. Install Softwares:

Install the following tools and softwares to your local machine:

0. Convert poetry packages into requirements file

```
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

1. Database management system:
   
+ [PostgreSQL](https://www.postgresql.org/download/)

2. GUI Administration and management tool for PostgreSQL

+ [PgAdmin4](https://www.postgresql.org/download/)

3. Python dependencies and packages managements:

+ [Poetry](https://python-poetry.org/docs/)

4. [Optional] Work with AWS Services from CLI:

+ [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html)

### 2. Virtual Environment:

+ Install the dependencies listed in the pyproject.toml file and lock them in the poetry.lock file into your virtual environment.

```
poetry install
```

+  create and activate a virtual environment

```
poetry shell
```


### 3. Database connection:

1. Make db connection:
Please refer to this [guide](https://github.com/LouisAnhTran/all-ai-platform-capstone-backend/blob/main/documentation/database_connection_guide.pdf)

3. Connection test:
Run this command to make sure the db connection is established correctly
```
poetry run python src/database/db_connection/test_connection.py
```

### 4. Run Backend:

+ run the app

```
poetry run python main.py
```

### 5. Test API:

+ access Swagger UI from your browser

```
http://loalhost:8000/docs
```

### 6. Build and Deploy:

```
 ./scripts/build_and_deploy/build_and_deploy.sh 
```
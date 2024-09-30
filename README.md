# ReferendumApi

## Prerequisites
* Python 3.9 or later
* Docker and Docker Compose


## Usage

Build the Docker images:
   ```
   make build
   ```

### Running Locally

To start the application, run:

```
make up
```

The API will be available at `http://localhost:80`.

Once the application is running, you can access the API documentation at `http://localhost:80/docs`

To stop the application, use:

```
make down
```

### Running Tests

To run the test suite, use:

```
make test
```

This command will build the necessary Docker images (if not already built) and run the tests in a separate container.

## Deployment

The API image is built with GitHub Actions, pushed to ECR, and then deployed on an EC2 server

### Environments

Both environments are run on the same server, with different tags and ports

- **Production**: Deployed automatically on pushes to the main branch, runs on port 80
- **Test**: Can be deployed manually using the workflow dispatch feature, runs on port 8080

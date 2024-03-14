# GenericSuite (backend version)
The GenericSuite for Python (backend version).

![GenericSuite Logo](https://github.com/tomkat-cr/genericsuite-fe/blob/main/src/lib/images/gs_logo_circle.svg)

GenericSuite is a versatile backend solution, designed to provide a comprehensive suite of features for Python APIs. It supports various frameworks including Chalice, FastAPI, and Flask, making it adaptable to a range of projects. This repository contains the backend logic, utilities, and configurations necessary to build and deploy scalable and maintainable applications.

## Features

- **Framework Agnostic**: Supports Chalice, FastAPI, and Flask frameworks.
- **Database Support**: Includes abstracted database operations for both MongoDB and DynamoDB, offering flexibility in choosing the database.
- **Authentication**: Implements JWT-based authentication, providing secure access to endpoints.
- **Dynamic Endpoint Creation**: Allows for defining endpoints dynamically through JSON configurations.
- **Utilities**: A collection of utilities for tasks such as sending emails, parsing multipart data, handling passwords, and more.
- **Billing Utilities**: Tools for managing billing plans and user subscriptions.
- **Menu Options**: Functionality to manage and retrieve authorized menu options based on user roles.

## Pre-requisites

- Python >= 3.9 and < 4.0

## Installation

To use GenericSuite in your project, install it with the following command(s):

### From Pypi

#### Pip
```bash
pip install genericsuite
```

#### Pipenv
```bash
pipenv install genericsuite
```

#### Poetry
```bash
poetry add genericsuite
```

### From a specific branch in the repository, e.g. "branch_x"

#### Pip
```bash
pip install git+https://github.com/tomkat-cr/genericsuite-be@branch_x
```

#### Pipenv
```bash
pipenv install git+https://github.com/tomkat-cr/genericsuite-be@branch_x
```

#### Poetry
```bash
poetry add git+https://github.com/tomkat-cr/genericsuite-be@branch_x
```

## Configuration

Configure your application by setting up the necessary environment variables. Refer to the example `.env.example` file for the required variables.

## Usage

1. **Select Your Framework**: Depending on your project, choose between Chalice, FastAPI, or Flask.
2. **Define Endpoints**: Utilize the dynamic endpoint creation feature by defining your endpoints in a JSON configuration file.
3. **Database Operations**: Implement database operations using the provided abstracted functions for MongoDB and DynamoDB.
4. **Authentication**: Secure your endpoints with JWT-based authentication.

## Documentation

For detailed documentation on each feature and module, please refer to the inline comments and docstrings within the codebase.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

This project is developed and maintained by Carlos J. Ramirez. For more information or to contribute to the project, visit [GenericSuite on GitHub](https://github.com/tomkat-cr/genericsuite-be).

Happy Coding!
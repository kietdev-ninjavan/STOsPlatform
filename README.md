<h1 align="center">Platform of STOs Team</h1>

<p align="center">
    <a href="https://www.python.org/downloads/release/python-31110/"><img alt="Python versions" src="https://img.shields.io/badge/python-3.11.10-blue"></a>
    <a href="https://docs.djangoproject.com/en/5.1/"><img alt="Documentation" src="https://img.shields.io/badge/django-5.1.1-darkgreen"></a>
</p>

# Introduction

Welcome to STOsPlatform, an internal project developed for the Opex & Ops Support (System Ops) team at NinjaVan Vietnam.
This platform is designed to streamline and optimize the operational tools and systems used by the team, enhancing
efficiency and improving workflows.

## Purpose

The primary goal of STOsPlatform is to provide the System Ops team with a centralized, user-friendly platform for
managing and operating various tools that are essential to daily operations. It serves as an internal hub for handling
tasks and automating processes, reducing manual effort and minimizing errors.

# Note:

- PLease update requirements.txt file after installing new packages
- Please update the .env file after changing the environment variables

# Code Conventions

- Please follow the PEP8 code conventions for Python
- Please document your code properly
- Run `flake8 .` to check before pushing the code
   ```bash
   flake8 .
   ```
---
# Running the Project

To run the project locally, follow the steps below:

## Django Server

1. Clone the repository:

    ```bash
    git clone https://github.com/kietdev-ninjavan/STOsPlatform.git
    ```
2. Create a virtual environment and activate it:
    - For virtualenv:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    - For conda
        ```bash
        conda create -n stos_platform python=3.11.10
        conda activate stos_platform
        ```

3. Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```
4. Create a `.env` file in the root directory of the project and add the following file `env.example`:

   ```bash
   cp env.example .env
   ```

5. Run the migrations:

    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

6. Create a superuser:

    ```bash
    python manage.py createsuperuser
    ```
7. Run the development server:

    ```bash
    python manage.py runserver
    ```
---
# For any questions, please contact System Ops Team Vietnam. Thank you!
   
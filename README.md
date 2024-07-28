# Solidus Hackathon

This repository contains the backend code for the Solidus Hackathon project, built using FastAPI.

## Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/oyeadii/solidus-hackathon.git
    cd solidus-backend
    ```

2. **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. **Install the dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

1. **Set up the environment variables** (see [Environment Variables](#environment-variables) section).

2. **Run the application**:
    ```bash
    uvicorn main:app --reload
    ```

   The application will be available at `http://127.0.0.1:8000`.

## Environment Variables

```
$ CONFIG='{"ENVI":"DEV","PYTHON_HOST": "localhost","PYTHON_USE_HTTPS": false,"PYTHON_PORT": 8888,"MODEL_NAME": "<model_want_to_use>","API_KEY":"<model_api_key>","PYTHON_TOKEN":<jupyter_notebook_token_here>}'
``` 

## Setting Up a Jupyter Notebook Client

To set up a Jupyter Notebook client in the same directory as the Solidus Backend project, follow these steps:

1. **Install Jupyter Notebook**:
    If you haven't already, you need to install Jupyter Notebook. You can do this using pip:
    ```bash
    pip install notebook
    ```

2. **Start Jupyter Notebook**:
    Navigate to the project directory and start the Jupyter Notebook server:
    ```bash
    jupyter notebook
    ```

3. **Access Jupyter Notebook**:
    After running the above command, your default web browser will open and you will be able to access the Jupyter Notebook interface. Copy the token to config and set in `PYTHON_TOKEN` key.
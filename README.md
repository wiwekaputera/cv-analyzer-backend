# CV Analyzer Backend

![Python](https://img.shields.io/badge/python-3.13-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0-black.svg)
![uv](https://img.shields.io/badge/uv-0.1-green.svg)
![PostgreSQL](https://img.shields.io/badge/postgresql-15-blue.svg)

A Flask-based backend service designed to analyze a large dataset of resumes against a given set of keywords, returning a ranked list of the most suitable candidates.

This project adheres to modern backend development practices, including the use of an application factory pattern, environment-based configuration, and comprehensive logging.

## Core Features

- **Keyword-Based Analysis:** A core API endpoint (`/api/analyze`) that accepts a list of keywords.
- **Candidate Ranking:** Implements logic to score and rank candidates based on keyword occurrences in their resume text.
- **Data Management:** Manages all candidate and resume metadata in a PostgreSQL database.
- **File Serving:** Hosts and serves the original resume PDF files via cloud storage.
- **Structured Logging:** Configured for both console and file-based logging for easy debugging and monitoring.
- **Database Seeding:** Includes a comprehensive script to populate the database and storage from a source dataset.

## Tech Stack

| Component                  | Technology / Library            |
| -------------------------- | ------------------------------- |
| **Language**               | Python 3.13                     |
| **Web Framework**          | Flask                           |
| **Environment & Packages** | `uv`                            |
| **Database**               | PostgreSQL (hosted on Supabase) |
| **File Storage**           | Supabase Storage                |
| **Data Validation**        | Pydantic                        |
| **Configuration**          | `python-decouple`               |

## Getting Started

Follow these instructions to get the project running on your local machine for development and testing.

### Prerequisites

- Python 3.13+
- `uv` package manager (`pip install uv`)

### Installation

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/wiwekaputera/cv-analyzer-backend.git](https://github.com/wiwekaputera/cv-analyzer-backend.git)
    cd cv-analyzer-backend
    ```

2.  **Install dependencies:**
    `uv` will create a virtual environment and install all required packages from `pyproject.toml`.

    ```bash
    uv sync
    ```

3.  **Configure Environment Variables:**
    Create a `.env` file in the root of the project. You can copy the example file:

    ```bash
    cp .env.example .env
    ```

    Then, fill in the values in your new `.env` file with your credentials from Supabase.

4.  **Database Seeding:**
    This is a one-time setup to populate your database and file storage.

    - Download the "Resume Dataset" from Kaggle and place the unzipped `ResumeDataset` folder in the project root.
    - Run the seeding script:
      ```bash
      uv run python seed_database.py
      ```

5.  **Run the Development Server:**
    ```bash
    uv run python run.py
    ```
    The server will start and be available at `http://localhost:5000`.

## Project Structure

This project is built using professional Flask patterns to ensure the code is modular, scalable, and easy to maintain.

- **Application Factory Pattern:** The Flask app is created within a `create_app()` function. This allows for easy configuration management for different environments (development, testing, production).
- **Blueprints:** API routes are organized into a `Blueprint` (`api_bp`). This decouples the routes from the main application setup, keeping the codebase clean.

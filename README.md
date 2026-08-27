# Task API

A simple CRUD API built with FastAPI and PostgreSQL.

This project started as an in-memory CRUD API in Assignment 1. In Assignment 2, the in-memory storage was replaced with a database repository. In Assignment 3, the application was containerized with Docker and PostgreSQL.

The service and API routes were kept unchanged while the repository implementation was switched to PostgreSQL.

## Technologies

- Python
- FastAPI
- PostgreSQL
- Docker
- Docker Compose
- Psycopg

## Project Structure

```text
.
├── main.py
├── service.py
├── repository.py
├── init.sql
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env
├── .env.example
└── README.md
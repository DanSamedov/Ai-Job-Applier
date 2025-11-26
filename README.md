# Automated AI Job Applier

> *This project is currently being actively developed.*

## Overview
The **Automated AI Job Applier** is a data engineering solution designed to streamline the job application process. It acts as a personal recruiting assistant that autonomously scrapes job listings, normalizes the data, analyzes fit using LLMs (Gemini API), and automates outreach.

Unlike simple "apply all" bots, this system prioritizes **quality over quantity** by using AI to match user experience with job descriptions before initiating contact.

## Key Features
* **Targeted Scraping:** Selenium-based scrapers (managed via Celery tasks) to extract listings from major job boards.
* **Data Normalization:** Pipelines to standardize raw HTML data into structured JSON/SQL formats.
* **AI Analysis:** Integrates **Google Gemini API** to score job descriptions against the user's resume and generate tailored cover letters.
* **Duplicate Detection:** Uses **Redis** caching to prevent processing the same listing twice.
* **Automated Outreach:** (In Development) Auto-fills application forms or sends email drafts to HR departments.

## Tech Stack
* **Language:** Python 3.10+
* **Orchestration:** Celery, Redis
* **Database:** PostgreSQL, SQLAlchemy
* **Browser Automation:** Selenium / WebDriver
* **AI Integration:** Google Gemini API
* **Containerization:** Docker, Docker Compose
* **Testing:** Pytest

## Architecture
The system follows a microservices-like architecture containerized with Docker:
1.  **Scraper Worker:** Periodically fetches raw job HTML.
2.  **Parser Service:** Cleans data and saves it to PostgreSQL.
3.  **Analyzer Agent:** Queries the Gemini API to score the job relevance (0-100%).
4.  **Application Bot:** Triggers actions for high-scoring (>85%) jobs.

# Overview

This AI-powered interior design assistant, built with Streamlit, helps users analyze and reimagine their living spaces. It leverages Google Gemini 2.5 Pro for room analysis and DALL-E 3 for generating photorealistic design visualizations. The application provides professional design feedback, generates design variants, allows side-by-side comparison, offers material shopping lists, estimates renovation costs, and enables saving, loading, and exporting design packages as PDF reports.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Framework
The application uses Streamlit, chosen for rapid prototyping and built-in state management via `st.session_state`. A wide layout (`layout="wide"`) is used for side-by-side image comparison.

## AI Processing Pipeline
The application uses a two-stage AI workflow:
1.  **Analysis Stage** (Google Gemini 2.5 Pro): Analyzes uploaded room images and user input to provide structured design analysis. It processes both image data and text, returning a JSON-formatted analysis.
2.  **Generation Stage** (DALL-E 3): Converts design recommendations into optimized DALL-E prompts using AI, generating photorealistic interior design visualizations. This stage also includes a refinement step where Gemini Vision analyzes generated designs to improve prompts.

## State Management
`st.session_state` is used for managing application state, storing analysis results, and maintaining data across user interactions to prevent redundant API calls.

## Module Organization
The codebase is organized into focused modules:
-   **app.py**: Main UI, user interactions, and workflow orchestration.
-   **prompts.py**: Stores system prompts as constants.
-   **utils.py**: Contains reusable API wrapper functions.
-   **database.py**: Handles database models and session management with SQLAlchemy.
-   **pdf_generator.py**: Manages PDF report generation.

## Image Processing
Images are converted to base64 encoding for API compatibility. The application supports PIL-compatible image formats.

## Error Handling
API calls are wrapped in try-except blocks, with error messages propagated to the UI.

## Database Architecture
PostgreSQL is used for project persistence, with tables for `projects` (project metadata, analysis, images, `user_id`), `design_variants` (generated images, prompts), and `recommendations` (material recommendations, shopping lists). This supports saving/loading projects, comparing iterations, and project history.

## UI/UX Decisions
-   **Auto-load and Auto-save**: Projects load automatically upon selection and save automatically after key actions (analysis, generation, refinements, recommendations).
-   **Prompt Editing**: Users can edit DALL-E prompts inline within the design variants section.
-   **Localization**: The application is localized to Russian, including UI elements and PDF content.
-   **Refinement UI**: Refinement options are displayed inline next to each design variant for improved usability.
-   **PDF Export**: Optimized for performance with a two-step generation and caching process, including Cyrillic font support and Markdown processing.
-   **Multi-User Support**: Simple username-based authentication (`user_id`) ensures project data isolation.

# External Dependencies

## Google Cloud Platform
-   **Google Gemini 2.5 Pro**: Used for multimodal image analysis and refining design prompts.

## OpenAI Platform
-   **DALL-E 3**: Generates photorealistic interior design images.

## Python Libraries
-   **streamlit**: Web application framework.
-   **google-genai**: Google Gemini API client.
-   **openai**: OpenAI Python client.
-   **Pillow**: Image manipulation.
-   **python-dotenv**: Environment variable management.
-   **sqlalchemy**: Database ORM.
-   **psycopg2-binary**: PostgreSQL adapter.
-   **reportlab**: PDF generation.
-   **httpx**: HTTP client.

## Environment Configuration
API authentication and database connection strings are managed via environment variables (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `DATABASE_URL`) loaded using `python-dotenv`.
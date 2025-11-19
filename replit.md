# Overview

This AI-powered interior design assistant, built with Streamlit, helps users analyze and reimagine their living spaces. It leverages Google Gemini 2.5 Pro for room analysis and Google Gemini 2.5 Flash Image for generating photorealistic design visualizations using image-to-image generation. The application provides professional design feedback, generates design variants, allows side-by-side comparison, offers material shopping lists, estimates renovation costs, and enables saving, loading, and exporting design packages as PDF reports.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Framework
The application uses Streamlit, chosen for rapid prototyping and built-in state management via `st.session_state`. A wide layout (`layout="wide"`) is used for side-by-side image comparison.

## AI Processing Pipeline
The application uses Google Gemini exclusively for all AI operations:
1.  **Analysis Stage** (Google Gemini 2.5 Pro): Analyzes uploaded room images and user input to provide structured design analysis. It processes both image data and text, returning a JSON-formatted analysis.
2.  **Prompt Generation Stage** (Google Gemini 2.5 Pro): Creates detailed prompts for image generation based on room analysis, user style preferences, and design requirements.
3.  **Image Generation Stage** (Google Gemini 2.5 Flash Image): Uses image-to-image generation to transform the uploaded room photo based on design prompts. The function accepts the original room image and a text prompt, converting both to the required format and sending them to the Gemini API. Generated images are returned as base64-encoded data URLs for display.
4.  **Refinement Stage** (Google Gemini 2.5 Pro): Analyzes generated designs and creates improved prompts based on user feedback.
5.  **Recommendations Stage** (Google Gemini 2.5 Pro): Generates detailed material recommendations and shopping lists based on the final design.

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
-   **Prompt Editing**: Users can edit image generation prompts inline within the design variants section.
-   **No Preset Styles**: Style selection starts empty, allowing users to choose their own preferences without defaults.
-   **Localization**: The application is localized to Russian, including UI elements and PDF content.
-   **Refinement UI**: Refinement options are displayed inline next to each design variant for improved usability.
-   **PDF Export**: Optimized for performance with a two-step generation and caching process, including Cyrillic font support and Markdown processing.
-   **Multi-User Support**: Simple username-based authentication (`user_id`) ensures project data isolation.

# External Dependencies

## Google Cloud Platform
-   **Google Gemini 2.5 Pro**: Used for multimodal image analysis and refining design prompts.
-   **Google Gemini 2.5 Flash Image**: Image-to-image generation model that transforms uploaded room photos based on design prompts while preserving structural geometry.

## Python Libraries
-   **streamlit**: Web application framework.
-   **google-genai**: Google Gemini API client (unified API for all AI operations).
-   **Pillow**: Image manipulation.
-   **python-dotenv**: Environment variable management.
-   **sqlalchemy**: Database ORM.
-   **psycopg2-binary**: PostgreSQL adapter.
-   **reportlab**: PDF generation.
-   **httpx**: HTTP client.

## Environment Configuration
API authentication and database connection strings are managed via environment variables:
-   **GEMINI_API_KEY**: Google Gemini API key for all AI operations (analysis, prompt generation, image generation, refinement, recommendations).
-   **DATABASE_URL**: PostgreSQL connection string for project persistence.

# Recent Changes

## November 19, 2025 - Complete Migration to Google Gemini
Completed full migration from OpenAI to Google Gemini for all AI operations:
- **Removed OpenAI dependency**: Eliminated all OpenAI API calls and dependencies
- **Unified AI pipeline**: All AI operations now use Google Gemini exclusively:
  - Room analysis: Gemini 2.5 Pro
  - Prompt generation: Gemini 2.5 Pro
  - Image generation: Gemini 2.5 Flash Image (image-to-image)
  - Design refinement: Gemini 2.5 Pro
  - Recommendations & shopping lists: Gemini 2.5 Pro
- **UI/UX improvement**: Removed default style selection ("Scandinavian"), now starts with empty selection for better user control
- **Simplified environment**: Only GEMINI_API_KEY required, no OpenAI credentials needed
- **Code cleanup**: Removed unused OpenAI functions and imports from utils.py and app.py
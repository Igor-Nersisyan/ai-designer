# Overview

This is an AI-powered interior design assistant built with Streamlit that helps users analyze and reimagine their living spaces. The application uses OpenAI's GPT-4o Vision to analyze uploaded room photos, providing professional design feedback, and DALL-E 3 to generate photorealistic visualizations of proposed renovations. Users can upload images, receive detailed architectural analysis, generate design variants, compare options side-by-side, get material shopping lists, estimate renovation costs, save/load projects, and export complete design packages as PDF reports.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Framework
The application uses Streamlit as the web framework, providing a simple Python-based UI with minimal boilerplate. Streamlit was chosen for its rapid prototyping capabilities and built-in state management through `st.session_state`, which eliminates the need for complex frontend frameworks or custom state management solutions.

**Key architectural decision**: Wide layout (`layout="wide"`) to accommodate side-by-side image comparison between original and generated designs.

## AI Processing Pipeline
The application implements a two-stage AI workflow:

1. **Analysis Stage** (GPT-4o Vision): 
   - Analyzes uploaded room images using multimodal capabilities
   - Processes both image data (base64-encoded) and user text input
   - Returns structured design analysis with specific sections (audit, problems, potential, recommendations)

2. **Generation Stage** (DALL-E 3):
   - Converts design recommendations into optimized DALL-E prompts via GPT-4o
   - Generates photorealistic interior design visualizations

**Rationale**: Separating analysis and generation allows for iterative refinement and gives users control over the creative direction before committing to image generation.

## State Management
Session state (`st.session_state`) stores the analysis results between reruns, preventing redundant API calls when users interact with the UI. This pattern is essential in Streamlit to maintain data across user interactions.

## Module Organization
Code is separated into focused modules:

- **app.py**: Main UI logic, layout, user interactions, and workflow orchestration
- **prompts.py**: System prompts as constants for maintainability and version control
- **utils.py**: Reusable API wrapper functions (image encoding, OpenAI API calls)
- **database.py**: PostgreSQL database models and session management using SQLAlchemy
- **pdf_generator.py**: PDF report generation using ReportLab

**Benefits**: Clear separation of concerns, easier testing, and simplified prompt engineering iterations without touching application logic.

## Image Processing
Images are converted to base64 encoding for GPT-4o Vision API compatibility. The application accepts PIL-compatible image formats through Streamlit's file uploader.

## Error Handling
API calls are wrapped in try-except blocks within utility functions, with error messages propagated to the UI layer for user-friendly display.

# External Dependencies

## OpenAI Platform
- **GPT-4o** (model: "gpt-4o"): Multimodal model for image analysis and text generation
  - Vision API: Analyzes room photos with structured prompts
  - Text API: Engineers optimized DALL-E prompts
  - Configuration: max_tokens=2000, temperature=0.7
- **DALL-E 3**: Generates photorealistic interior design images (implementation pending in current codebase)

## Python Libraries
- **streamlit** (1.32.0): Web application framework
- **openai** (1.12.0): Official OpenAI Python client
- **Pillow** (10.2.0): Image manipulation and format handling
- **python-dotenv** (1.0.1): Environment variable management for API key security
- **sqlalchemy** (2.0.44): Database ORM for project persistence
- **psycopg2-binary** (2.9.11): PostgreSQL adapter for Python
- **reportlab** (4.4.4): PDF generation library
- **httpx** (0.27.2): HTTP client (pinned for OpenAI compatibility)

## Database Architecture
Uses PostgreSQL for project persistence with three main tables:
- **projects**: Stores project metadata, room analysis, and base64-encoded images
- **design_variants**: Stores generated design images with prompts and iteration counts
- **recommendations**: Stores material recommendations and shopping lists

**Rationale**: Enables users to save/load projects across sessions, compare multiple design iterations, and maintain project history.

## Environment Configuration
API authentication uses environment variables loaded via dotenv, keeping sensitive credentials out of version control. Required variables:
- `OPENAI_API_KEY`: OpenAI API authentication
- `DATABASE_URL`: PostgreSQL connection string (auto-configured by Replit)

# Recent Changes (November 15, 2025)

## Phase 2 Features Implemented
1. **Project Persistence**: Full save/load functionality with PostgreSQL database
2. **Design Comparison**: Side-by-side variant comparison view
3. **Shopping List Generator**: AI-powered material shopping lists with store links
4. **Budget Calculator**: Interactive renovation cost estimation with category breakdowns
5. **PDF Export**: Complete design packages with images and recommendations
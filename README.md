# Business Admin Demo

A demo application showcasing [starlette-admin](https://github.com/jowilf/starlette-admin) - a fast, beautiful, and extensible administrative interface framework for Starlette & FastAPI applications.

## Features

- **Category Management**: Organize products into categories
- **Product Catalog**: Manage products with pricing, stock, and SKU
- **Customer Database**: Track customer information and VIP status
- **Order Management**: Handle orders with multiple items and status tracking

## Quick Start

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python app.py
```

Or using uvicorn directly:

```bash
uvicorn app:app --reload
```

### 4. Access the Admin Interface

Open your browser and navigate to: **http://localhost:8000/admin**

## Project Structure

```
plalace-business/
├── app.py              # Main application with models and admin views
├── requirements.txt    # Python dependencies
├── business.db         # SQLite database (auto-created)
└── README.md           # This file
```

## Database Models

| Model | Description |
|-------|-------------|
| Category | Product categories with name and description |
| Product | Products with pricing, stock, and category relationship |
| Customer | Customer information including VIP status |
| Order | Customer orders with status tracking |
| OrderItem | Individual items within an order |

## Sample Data

The application automatically seeds sample data on first run, including:
- 4 categories (Electronics, Clothing, Books, Home & Garden)
- 7 products across categories
- 3 customers
- 3 orders with items

## Admin Features

- **CRUD Operations**: Create, Read, Update, Delete for all models
- **Search & Filter**: Search across multiple fields
- **Sorting**: Sort by various columns
- **Export**: Export data to CSV/Excel/PDF
- **Relationships**: Navigate between related records
- **Responsive**: Works on desktop and mobile

## Technologies

- [Starlette](https://www.starlette.io/) - Web framework
- [starlette-admin](https://github.com/jowilf/starlette-admin) - Admin interface
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM
- [SQLite](https://www.sqlite.org/) - Database
- [Uvicorn](https://www.uvicorn.org/) - ASGI server


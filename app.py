"""
Starlette-Admin Demo - Booking Management System
A sample admin interface for managing fitness/wellness bookings.
"""

import os
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional
import random
import json

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum as SQLEnum,
    Float,
    Integer,
    String,
    Time,
    create_engine,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import RedirectResponse, JSONResponse, HTMLResponse
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from starlette_admin.views import Link
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.fields import (
    IntegerField,
    StringField,
    DateField,
    TimeField,
    EnumField,
    DecimalField,
)


# =============================================================================
# Configuration
# =============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# =============================================================================
# Database Models
# =============================================================================

class Base(DeclarativeBase):
    pass


class ServiceModality(str, Enum):
    STRENGTH = "Strength"
    PILATES = "Pilates"
    YOGA = "Yoga"
    PHYSIOTHERAPY = "Physiotherapy"
    HYROX = "Hyrox"


class BookingStatus(str, Enum):
    UPCOMING = "Upcoming"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class PaymentMethod(str, Enum):
    CREDIT_CARD = "Credit Card"
    PACKAGE = "Package"


class Space(str, Enum):
    PALACE_1 = "Palace 1"
    PALACE_2 = "Palace 2"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Customer Information
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Service & Space
    service: Mapped[ServiceModality] = mapped_column(SQLEnum(ServiceModality), nullable=False)
    space: Mapped[Space] = mapped_column(SQLEnum(Space), nullable=False)
    
    # Date & Time
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    time_from: Mapped[time] = mapped_column(Time, nullable=False)
    time_to: Mapped[time] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Status & Payment
    status: Mapped[BookingStatus] = mapped_column(SQLEnum(BookingStatus), default=BookingStatus.UPCOMING)
    payment_method: Mapped[PaymentMethod] = mapped_column(SQLEnum(PaymentMethod), nullable=False)
    
    # Revenue
    revenue: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __str__(self) -> str:
        return f"Booking #{self.id} - {self.customer_name}"


# =============================================================================
# Database Setup
# =============================================================================

DATABASE_URL = "sqlite:///./bookings.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_db():
    """Initialize database and create tables."""
    Base.metadata.create_all(engine)


def seed_sample_data():
    """Seed the database with sample booking data."""
    
    with Session(engine) as session:
        # Check if data already exists
        if session.query(Booking).first():
            return
        
        # Sample customer data
        customers = [
            ("Emily Chen", "+852 9123 4567"),
            ("Michael Wong", "+852 9234 5678"),
            ("Sarah Lam", "+852 9345 6789"),
            ("David Lee", "+852 9456 7890"),
            ("Jessica Tam", "+852 9567 8901"),
            ("Kevin Ng", "+852 9678 9012"),
            ("Rachel Ho", "+852 9789 0123"),
            ("Alex Chan", "+852 9890 1234"),
            ("Sophia Liu", "+852 9901 2345"),
            ("James Yip", "+852 9012 3456"),
        ]
        
        # Service pricing (per hour)
        service_rates = {
            ServiceModality.STRENGTH: 450,
            ServiceModality.PILATES: 550,
            ServiceModality.YOGA: 400,
            ServiceModality.PHYSIOTHERAPY: 800,
            ServiceModality.HYROX: 600,
        }
        
        # Generate bookings for the past month and upcoming week
        bookings = []
        today = date.today()
        
        # Time slots (hour, minute)
        time_slots = [
            (7, 0), (8, 0), (9, 0), (10, 0), (11, 0),
            (14, 0), (15, 0), (16, 0), (17, 0), (18, 0), (19, 0), (20, 0)
        ]
        
        # Durations in minutes
        durations = [30, 45, 60, 90]
        
        # Past bookings (completed or cancelled) - last 30 days
        for days_ago in range(30, 0, -1):
            booking_date = today - timedelta(days=days_ago)
            num_bookings = random.randint(6, 14)
            
            for _ in range(num_bookings):
                customer = random.choice(customers)
                service = random.choice(list(ServiceModality))
                space = random.choice(list(Space))
                slot = random.choice(time_slots)
                duration = random.choice(durations)
                
                time_from = time(slot[0], slot[1])
                end_hour = slot[0] + (slot[1] + duration) // 60
                end_minute = (slot[1] + duration) % 60
                time_to = time(min(end_hour, 23), end_minute)
                
                # 85% completed, 15% cancelled for past bookings
                status = BookingStatus.CANCELLED if random.random() < 0.15 else BookingStatus.COMPLETED
                
                payment = random.choice(list(PaymentMethod))
                rate = service_rates[service]
                revenue = (rate * duration / 60) if status != BookingStatus.CANCELLED else 0
                
                bookings.append(Booking(
                    customer_name=customer[0],
                    customer_phone=customer[1],
                    service=service,
                    space=space,
                    booking_date=booking_date,
                    time_from=time_from,
                    time_to=time_to,
                    duration_minutes=duration,
                    status=status,
                    payment_method=payment,
                    revenue=revenue,
                    created_at=datetime.combine(booking_date, time_from) - timedelta(days=random.randint(1, 7))
                ))
        
        # Today's bookings (mix of completed, active, upcoming)
        current_hour = datetime.now().hour
        for slot in time_slots:
            if random.random() < 0.7:  # 70% chance of booking for each slot
                for space in list(Space):
                    if random.random() < 0.6:  # 60% chance per space
                        customer = random.choice(customers)
                        service = random.choice(list(ServiceModality))
                        duration = random.choice(durations)
                        
                        time_from = time(slot[0], slot[1])
                        end_hour = slot[0] + (slot[1] + duration) // 60
                        end_minute = (slot[1] + duration) % 60
                        time_to = time(min(end_hour, 23), end_minute)
                        
                        # Determine status based on current time
                        if slot[0] < current_hour:
                            status = BookingStatus.COMPLETED
                        elif slot[0] == current_hour:
                            status = BookingStatus.ACTIVE
                        else:
                            status = BookingStatus.UPCOMING
                        
                        payment = random.choice(list(PaymentMethod))
                        rate = service_rates[service]
                        revenue = rate * duration / 60
                        
                        bookings.append(Booking(
                            customer_name=customer[0],
                            customer_phone=customer[1],
                            service=service,
                            space=space,
                            booking_date=today,
                            time_from=time_from,
                            time_to=time_to,
                            duration_minutes=duration,
                            status=status,
                            payment_method=payment,
                            revenue=revenue,
                            created_at=datetime.now() - timedelta(days=random.randint(1, 5))
                        ))
        
        # Future bookings (upcoming) - next 14 days
        for days_ahead in range(1, 15):
            booking_date = today + timedelta(days=days_ahead)
            num_bookings = random.randint(8, 16)
            
            for _ in range(num_bookings):
                customer = random.choice(customers)
                service = random.choice(list(ServiceModality))
                space = random.choice(list(Space))
                slot = random.choice(time_slots)
                duration = random.choice(durations)
                
                time_from = time(slot[0], slot[1])
                end_hour = slot[0] + (slot[1] + duration) // 60
                end_minute = (slot[1] + duration) % 60
                time_to = time(min(end_hour, 23), end_minute)
                
                payment = random.choice(list(PaymentMethod))
                rate = service_rates[service]
                revenue = rate * duration / 60
                
                bookings.append(Booking(
                    customer_name=customer[0],
                    customer_phone=customer[1],
                    service=service,
                    space=space,
                    booking_date=booking_date,
                    time_from=time_from,
                    time_to=time_to,
                    duration_minutes=duration,
                    status=BookingStatus.UPCOMING,
                    payment_method=payment,
                    revenue=revenue,
                    created_at=datetime.now() - timedelta(days=random.randint(0, 3))
                ))
        
        session.add_all(bookings)
        session.commit()
        print(f"✅ Seeded {len(bookings)} sample bookings!")


# =============================================================================
# Dashboard Data API
# =============================================================================

def get_dashboard_data(start_date: date, end_date: date) -> dict:
    """Calculate dashboard metrics for the given date range."""
    
    with Session(engine) as session:
        # Operating hours per day (7am to 9pm = 14 hours = 840 minutes)
        DAILY_OPERATING_MINUTES = 840
        
        # Get all bookings in date range (excluding cancelled)
        bookings = session.query(Booking).filter(
            Booking.booking_date >= start_date,
            Booking.booking_date <= end_date,
            Booking.status != BookingStatus.CANCELLED
        ).all()
        
        # Calculate days in range
        days_in_range = (end_date - start_date).days + 1
        
        # =====================================================================
        # Space Utilization Rate
        # =====================================================================
        space_data = {}
        for space in Space:
            space_bookings = [b for b in bookings if b.space == space]
            total_booked_minutes = sum(b.duration_minutes for b in space_bookings)
            max_capacity_minutes = DAILY_OPERATING_MINUTES * days_in_range
            utilization = (total_booked_minutes / max_capacity_minutes * 100) if max_capacity_minutes > 0 else 0
            space_revenue = sum(b.revenue for b in space_bookings)
            
            space_data[space.value] = {
                "utilization": round(utilization, 1),
                "booked_hours": round(total_booked_minutes / 60, 1),
                "total_bookings": len(space_bookings),
                "revenue": round(space_revenue, 2)
            }
        
        # =====================================================================
        # Daily Revenue (for chart)
        # =====================================================================
        daily_revenue = []
        current_date = start_date
        while current_date <= end_date:
            day_bookings = [b for b in bookings if b.booking_date == current_date]
            day_revenue = sum(b.revenue for b in day_bookings)
            daily_revenue.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "day": current_date.strftime("%a"),
                "revenue": round(day_revenue, 2),
                "bookings": len(day_bookings)
            })
            current_date += timedelta(days=1)
        
        # =====================================================================
        # Modality Performance
        # =====================================================================
        modality_data = {}
        total_revenue = sum(b.revenue for b in bookings)
        total_booked_minutes = sum(b.duration_minutes for b in bookings)
        
        for service in ServiceModality:
            service_bookings = [b for b in bookings if b.service == service]
            service_minutes = sum(b.duration_minutes for b in service_bookings)
            service_revenue = sum(b.revenue for b in service_bookings)
            
            # Utilization as percentage of total booked time
            utilization = (service_minutes / total_booked_minutes * 100) if total_booked_minutes > 0 else 0
            # Revenue distribution
            revenue_share = (service_revenue / total_revenue * 100) if total_revenue > 0 else 0
            
            modality_data[service.value] = {
                "bookings": len(service_bookings),
                "hours": round(service_minutes / 60, 1),
                "revenue": round(service_revenue, 2),
                "utilization": round(utilization, 1),
                "revenue_share": round(revenue_share, 1)
            }
        
        # =====================================================================
        # Summary Stats
        # =====================================================================
        summary = {
            "total_bookings": len(bookings),
            "total_revenue": round(total_revenue, 2),
            "total_hours": round(total_booked_minutes / 60, 1),
            "avg_daily_revenue": round(total_revenue / days_in_range, 2) if days_in_range > 0 else 0,
            "avg_daily_bookings": round(len(bookings) / days_in_range, 1) if days_in_range > 0 else 0
        }
        
        return {
            "summary": summary,
            "space_utilization": space_data,
            "daily_revenue": daily_revenue,
            "modality_performance": modality_data,
            "date_range": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d"),
                "days": days_in_range
            }
        }


# =============================================================================
# Admin Views
# =============================================================================

class BookingView(ModelView):
    """Admin view for Booking model with custom filtering."""
    
    name = "Booking"
    label = "Bookings"
    
    # Fields to display
    fields = [
        IntegerField("id", label="Booking ID"),
        StringField("customer_name", label="Customer Name"),
        StringField("customer_phone", label="Phone No."),
        EnumField("service", label="Service (Modality)", enum=ServiceModality),
        EnumField("space", label="Space", enum=Space),
        DateField("booking_date", label="Date"),
        TimeField("time_from", label="Time From"),
        TimeField("time_to", label="Time To"),
        IntegerField("duration_minutes", label="Duration (min)"),
        EnumField("status", label="Status", enum=BookingStatus),
        EnumField("payment_method", label="Payment Method", enum=PaymentMethod),
        DecimalField("revenue", label="Revenue (HKD)"),
    ]
    
    # Column labels for list view
    column_labels = {
        "id": "Booking ID",
        "customer_name": "Customer Name",
        "customer_phone": "Phone No.",
        "service": "Service",
        "space": "Space",
        "booking_date": "Date",
        "time_from": "From",
        "time_to": "To",
        "duration_minutes": "Duration",
        "status": "Status",
        "payment_method": "Payment",
        "revenue": "Revenue",
    }
    
    # Default sorting: latest to oldest by booking date, then by time
    fields_default_sort = [("booking_date", True), ("time_from", True)]
    
    # Searchable fields
    searchable_fields = ["customer_name", "customer_phone"]
    
    # Sortable fields
    sortable_fields = [
        "id",
        "customer_name",
        "service",
        "space",
        "booking_date",
        "time_from",
        "duration_minutes",
        "status",
        "payment_method",
        "revenue",
    ]
    
    # Fields to exclude from create/edit forms
    exclude_fields_from_list = ["created_at"]
    exclude_fields_from_create = ["id", "created_at"]
    exclude_fields_from_edit = ["id", "created_at"]


# =============================================================================
# Application Setup
# =============================================================================

# Initialize database
init_db()
seed_sample_data()

# Templates
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# Dashboard page handler
async def dashboard_page(request: Request):
    """Render the dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


# API endpoint for dashboard data
async def dashboard_api(request: Request):
    """API endpoint to fetch dashboard data."""
    # Default to last 7 days
    end_date = date.today()
    start_date = end_date - timedelta(days=6)
    
    # Check for query parameters
    if "start_date" in request.query_params:
        try:
            start_date = datetime.strptime(request.query_params["start_date"], "%Y-%m-%d").date()
        except:
            pass
    if "end_date" in request.query_params:
        try:
            end_date = datetime.strptime(request.query_params["end_date"], "%Y-%m-%d").date()
        except:
            pass
    
    data = get_dashboard_data(start_date, end_date)
    return JSONResponse(data)


# Create Starlette app
async def homepage(request):
    """Redirect to dashboard."""
    return RedirectResponse(url="/admin/dashboard")

app = Starlette(
    routes=[
        Route("/", homepage),
        Route("/admin/dashboard", dashboard_page),
        Route("/api/dashboard", dashboard_api),
    ],
    on_startup=[init_db],
)

# Create admin interface with custom templates
admin = Admin(
    engine,
    title="Palace Booking",
    templates_dir=os.path.join(BASE_DIR, "templates"),
    statics_dir=os.path.join(BASE_DIR, "statics"),
    logo_url="/admin/statics/images/desktopLogo.svg",
)

# Add views - Dashboard link first, then Bookings
admin.add_view(Link(label="Dashboard", icon="fa-solid fa-chart-line", url="/admin/dashboard"))
admin.add_view(BookingView(Booking, icon="fa-solid fa-calendar-check"))

# Mount admin to app
admin.mount_to(app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

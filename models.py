from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class SharkPupUser(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class SharkPup:
    """Represents a shark pup entry in the database."""
    
    def __init__(self, date, name, notes=None, length=None, weight=None, date_of_birth=None, mother_id=None, sex=None, researcher=None, status="live"):
        self.id = None  # Will be set when saved to the database
        self.date = date
        self.name = name
        self.length = float(length) if length is not None else None
        self.weight = float(weight) if weight is not None else None
        self.notes = notes
        self.date_of_birth = date_of_birth
        self.mother_id = mother_id
        self.sex = sex  # 'Male', 'Female', or None if unknown
        self.researcher = researcher  # Username of researcher who added the entry
        self.status = status  # 'live' or 'stillborn'
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        """Convert the SharkPup object to a dictionary for JSON storage."""
        return {
            "id": self.id,
            "date": self.date,
            "name": self.name,
            "length": self.length,
            "weight": self.weight,
            "notes": self.notes,
            "date_of_birth": self.date_of_birth,
            "mother_id": self.mother_id,
            "sex": self.sex,
            "researcher": self.researcher,
            "status": self.status,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a SharkPup object from a dictionary."""
        pup = cls(
            date=data["date"],
            name=data["name"],
            length=data.get("length"),
            weight=data.get("weight"),
            notes=data.get("notes"),
            date_of_birth=data.get("date_of_birth"),
            mother_id=data.get("mother_id"),
            sex=data.get("sex"),
            researcher=data.get("researcher"),
            status=data.get("status", "live")  # Default to 'live' if not specified
        )
        pup.id = data["id"]
        pup.created_at = data["created_at"]
        return pup

class FeedingSession:
    """Represents a feeding session for a shark pup."""
    
    def __init__(self, pup_id, date, session_notes=None, feeding_time="AM", researcher=None):
        self.id = None  # Will be set when saved to the database
        self.pup_id = pup_id
        self.date = date
        self.session_notes = session_notes
        self.feeding_time = feeding_time  # "AM" or "PM"
        self.food_items = []  # List of FoodItem objects
        self.researcher = researcher  # Username of researcher who recorded the session
        self.created_at = datetime.now().isoformat()
    
    def add_food_item(self, food_type, amount, notes=None):
        """Add a food item to this feeding session."""
        food_item = FoodItem(food_type=food_type, amount=amount, notes=notes)
        self.food_items.append(food_item)
        return food_item
    
    def to_dict(self):
        """Convert the FeedingSession object to a dictionary for JSON storage."""
        return {
            "id": self.id,
            "pup_id": self.pup_id,
            "date": self.date,
            "session_notes": self.session_notes,
            "feeding_time": self.feeding_time,
            "food_items": [item.to_dict() for item in self.food_items],
            "researcher": self.researcher,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a FeedingSession object from a dictionary."""
        session = cls(
            pup_id=data["pup_id"],
            date=data["date"],
            session_notes=data.get("session_notes"),
            feeding_time=data.get("feeding_time", "AM"),  # Default to AM for backward compatibility
            researcher=data.get("researcher")  # Researcher tracking
        )
        session.id = data["id"]
        session.created_at = data["created_at"]
        
        # Add food items
        for item_data in data.get("food_items", []):
            food_item = FoodItem.from_dict(item_data)
            session.food_items.append(food_item)
            
        return session
        
    def get_total_amount(self):
        """Calculate the total amount of food in this session."""
        return sum(item.amount for item in self.food_items)


class FoodItem:
    """Represents a food item in a feeding session."""
    
    def __init__(self, food_type, amount, notes=None):
        self.food_type = food_type
        self.amount = float(amount)
        self.notes = notes
    
    def to_dict(self):
        """Convert the FoodItem object to a dictionary for JSON storage."""
        return {
            "food_type": self.food_type,
            "amount": self.amount,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a FoodItem object from a dictionary."""
        return cls(
            food_type=data["food_type"],
            amount=data["amount"],
            notes=data.get("notes")
        )


# Keeping FeedingRecord for backward compatibility
class FeedingRecord:
    """Represents a feeding record for a shark pup (legacy)."""
    
    def __init__(self, pup_id, date, food_type, amount, notes=None):
        self.id = None  # Will be set when saved to the database
        self.pup_id = pup_id
        self.date = date
        self.food_type = food_type
        self.amount = float(amount)
        self.notes = notes
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        """Convert the FeedingRecord object to a dictionary for JSON storage."""
        return {
            "id": self.id,
            "pup_id": self.pup_id,
            "date": self.date,
            "food_type": self.food_type,
            "amount": self.amount,
            "notes": self.notes,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a FeedingRecord object from a dictionary."""
        record = cls(
            pup_id=data["pup_id"],
            date=data["date"],
            food_type=data["food_type"],
            amount=data["amount"],
            notes=data.get("notes")
        )
        record.id = data["id"]
        record.created_at = data["created_at"]
        return record

class TrainingRecord:
    """Represents a training record for a shark pup."""
    
    def __init__(self, pup_id, date, training_type, duration, progress, notes=None, researcher=None):
        self.id = None  # Will be set when saved to the database
        self.pup_id = pup_id
        self.date = date
        self.training_type = training_type
        self.duration = int(duration)  # duration in minutes
        self.progress = progress  # e.g., "Started", "In Progress", "Completed"
        self.notes = notes
        self.researcher = researcher  # Track which researcher created the record
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        """Convert the TrainingRecord object to a dictionary for JSON storage."""
        return {
            "id": self.id,
            "pup_id": self.pup_id,
            "date": self.date,
            "training_type": self.training_type,
            "duration": self.duration,
            "progress": self.progress,
            "notes": self.notes,
            "researcher": self.researcher,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a TrainingRecord object from a dictionary."""
        record = cls(
            pup_id=data["pup_id"],
            date=data["date"],
            training_type=data["training_type"],
            duration=data["duration"],
            progress=data["progress"],
            notes=data.get("notes"),
            researcher=data.get("researcher")
        )
        record.id = data["id"]
        record.created_at = data["created_at"]
        return record
        
class MeasurementRecord:
    """Represents a measurement record (weight and/or length) for a shark pup."""
    
    def __init__(self, pup_id, date, weight=None, length=None, notes=None):
        self.id = None  # Will be set when saved to the database
        self.pup_id = pup_id
        self.date = date
        self.weight = float(weight) if weight is not None else None  # weight in grams
        self.length = float(length) if length is not None else None  # length in cm
        self.notes = notes
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        """Convert the MeasurementRecord object to a dictionary for JSON storage."""
        return {
            "id": self.id,
            "pup_id": self.pup_id,
            "date": self.date,
            "weight": self.weight,
            "length": self.length,
            "notes": self.notes,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a MeasurementRecord object from a dictionary."""
        record = cls(
            pup_id=data["pup_id"],
            date=data["date"],
            weight=data.get("weight"),
            length=data.get("length"),
            notes=data.get("notes")
        )
        record.id = data["id"]
        record.created_at = data["created_at"]
        return record

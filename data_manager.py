import os
import json
import logging
from datetime import datetime
from models import SharkPup, FeedingRecord, TrainingRecord, FeedingSession, FoodItem, MeasurementRecord

class DataManager:
    """Handles data storage and retrieval for shark pups."""
    
    def __init__(self, data_file="shark_pups.json", feeding_file="feeding_records.json", 
                 training_file="training_records.json", feeding_sessions_file="feeding_sessions.json",
                 measurements_file="measurements.json"):
        self.data_file = data_file
        self.feeding_file = feeding_file
        self.training_file = training_file
        self.feeding_sessions_file = feeding_sessions_file
        self.measurements_file = measurements_file
        self.ensure_data_file_exists()
        self.ensure_feeding_file_exists()
        self.ensure_training_file_exists()
        # Make sure the feeding sessions file exists
        if not os.path.exists(self.feeding_sessions_file):
            with open(self.feeding_sessions_file, "w") as f:
                json.dump([], f)
        # Make sure the measurements file exists
        if not os.path.exists(self.measurements_file):
            with open(self.measurements_file, "w") as f:
                json.dump([], f)
    
    def ensure_data_file_exists(self):
        """Create the data file if it doesn't exist."""
        if not os.path.exists(self.data_file):
            with open(self.data_file, "w") as f:
                json.dump([], f)
    
    def ensure_feeding_file_exists(self):
        """Create the feeding records file if it doesn't exist."""
        if not os.path.exists(self.feeding_file):
            with open(self.feeding_file, "w") as f:
                json.dump([], f)
    
    def ensure_training_file_exists(self):
        """Create the training records file if it doesn't exist."""
        if not os.path.exists(self.training_file):
            with open(self.training_file, "w") as f:
                json.dump([], f)
    
    def get_all_pups(self):
        """Get all shark pups from the data file."""
        try:
            with open(self.data_file, "r") as f:
                pup_dicts = json.load(f)
                return [SharkPup.from_dict(pup_dict) for pup_dict in pup_dicts]
        except Exception as e:
            logging.error(f"Error reading shark pups data: {e}")
            return []
    
    def add_pup(self, pup):
        """Add a new shark pup to the data file."""
        try:
            pups = self.get_all_pups()
            
            # Set ID to be one more than the highest existing ID, or 1 if no pups exist
            max_id = max([p.id or 0 for p in pups], default=0) if pups else 0
            pup.id = max_id + 1
            
            pup_dicts = [p.to_dict() for p in pups]
            pup_dicts.append(pup.to_dict())
            
            with open(self.data_file, "w") as f:
                json.dump(pup_dicts, f, indent=2)
            
            return pup
        except Exception as e:
            logging.error(f"Error adding shark pup: {e}")
            return None
            
    def update_pup(self, pup_id, updated_data):
        """Update an existing shark pup record."""
        try:
            pups = self.get_all_pups()
            updated = False
            
            for i, pup in enumerate(pups):
                if pup.id == pup_id:
                    # Update fields with new data
                    if 'date' in updated_data:
                        pup.date = updated_data['date']
                    if 'name' in updated_data:
                        pup.name = updated_data['name']
                    if 'length' in updated_data:
                        pup.length = float(updated_data['length']) if updated_data['length'] != '' else None
                    if 'weight' in updated_data:
                        pup.weight = float(updated_data['weight']) if updated_data['weight'] != '' else None
                    if 'notes' in updated_data:
                        pup.notes = updated_data['notes']
                    if 'date_of_birth' in updated_data:
                        pup.date_of_birth = updated_data['date_of_birth'] if updated_data['date_of_birth'] != '' else None
                    if 'mother_id' in updated_data:
                        pup.mother_id = updated_data['mother_id'] if updated_data['mother_id'] != '' else None
                    if 'status' in updated_data:
                        pup.status = updated_data['status']
                    if 'sex' in updated_data:
                        pup.sex = updated_data['sex'] if updated_data['sex'] != '' else None
                    
                    pups[i] = pup
                    updated = True
                    break
            
            if updated:
                pup_dicts = [p.to_dict() for p in pups]
                with open(self.data_file, "w") as f:
                    json.dump(pup_dicts, f, indent=2)
                # Find the updated pup to return it
                for p in pups:
                    if p.id == pup_id:
                        return p
                return None
            else:
                logging.error(f"Shark pup with ID {pup_id} not found for updating")
                return None
                
        except Exception as e:
            logging.error(f"Error updating shark pup: {e}")
            return None
    
    def get_pup_by_id(self, pup_id):
        """Get a shark pup by ID."""
        try:
            pups = self.get_all_pups()
            for pup in pups:
                if str(pup.id) == str(pup_id):
                    return pup
            return None
        except Exception as e:
            logging.error(f"Error getting shark pup by ID: {e}")
            return None
    
    # Feeding Records Methods
    def get_all_feeding_records(self):
        """Get all feeding records from the feeding file."""
        try:
            with open(self.feeding_file, "r") as f:
                record_dicts = json.load(f)
                return [FeedingRecord.from_dict(record) for record in record_dicts]
        except Exception as e:
            logging.error(f"Error reading feeding records data: {e}")
            return []
    
    def get_feeding_records_by_pup_id(self, pup_id):
        """Get feeding records for a specific shark pup."""
        try:
            records = self.get_all_feeding_records()
            return [r for r in records if r.pup_id == pup_id]
        except Exception as e:
            logging.error(f"Error getting feeding records for pup ID {pup_id}: {e}")
            return []
    
    def add_feeding_record(self, record):
        """Add a new feeding record to the feeding file."""
        try:
            records = self.get_all_feeding_records()
            
            # Set ID to be one more than the highest existing ID, or 1 if no records exist
            max_id = max([r.id or 0 for r in records], default=0) if records else 0
            record.id = max_id + 1
            
            record_dicts = [r.to_dict() for r in records]
            record_dicts.append(record.to_dict())
            
            with open(self.feeding_file, "w") as f:
                json.dump(record_dicts, f, indent=2)
            
            return record
        except Exception as e:
            logging.error(f"Error adding feeding record: {e}")
            return None
    
    # Training Records Methods
    def get_all_training_records(self):
        """Get all training records from the training file."""
        try:
            with open(self.training_file, "r") as f:
                record_dicts = json.load(f)
                return [TrainingRecord.from_dict(record) for record in record_dicts]
        except Exception as e:
            logging.error(f"Error reading training records data: {e}")
            return []
    
    def get_training_records_by_pup_id(self, pup_id):
        """Get training records for a specific shark pup."""
        try:
            records = self.get_all_training_records()
            return [r for r in records if r.pup_id == pup_id]
        except Exception as e:
            logging.error(f"Error getting training records for pup ID {pup_id}: {e}")
            return []
    
    def add_training_record(self, record):
        """Add a new training record to the training file."""
        try:
            records = self.get_all_training_records()
            
            # Set ID to be one more than the highest existing ID, or 1 if no records exist
            max_id = max([r.id or 0 for r in records], default=0) if records else 0
            record.id = max_id + 1
            
            record_dicts = [r.to_dict() for r in records]
            record_dicts.append(record.to_dict())
            
            with open(self.training_file, "w") as f:
                json.dump(record_dicts, f, indent=2)
            
            return record
        except Exception as e:
            logging.error(f"Error adding training record: {e}")
            return None
            
    def get_training_record_by_id(self, record_id):
        """Get a training record by ID."""
        try:
            records = self.get_all_training_records()
            for record in records:
                if record.id == record_id:
                    return record
            return None
        except Exception as e:
            logging.error(f"Error getting training record by ID: {e}")
            return None
    
    def update_training_record(self, record_id, updated_data):
        """Update an existing training record."""
        try:
            records = self.get_all_training_records()
            record_to_update = None
            
            # Find the record to update
            for i, record in enumerate(records):
                if record.id == record_id:
                    record_to_update = record
                    records.remove(record)
                    break
                    
            if not record_to_update:
                return None
                
            # Update fields with new data
            if 'date' in updated_data:
                record_to_update.date = updated_data['date']
            if 'training_type' in updated_data:
                record_to_update.training_type = updated_data['training_type']
            if 'duration' in updated_data:
                record_to_update.duration = int(updated_data['duration'])
            if 'progress' in updated_data:
                record_to_update.progress = updated_data['progress']
            if 'notes' in updated_data:
                record_to_update.notes = updated_data['notes']
            
            # Add updated record back to the list
            records.append(record_to_update)
            
            # Save records
            record_dicts = [r.to_dict() for r in records]
            with open(self.training_file, "w") as f:
                json.dump(record_dicts, f, indent=2)
            
            return record_to_update
            
        except Exception as e:
            logging.error(f"Error updating training record: {e}")
            return None
            
    def delete_training_record(self, record_id):
        """Delete a training record."""
        try:
            records = self.get_all_training_records()
            original_count = len(records)
            
            # Filter out the record to delete
            records = [r for r in records if r.id != record_id]
            
            if len(records) < original_count:
                # Save the updated list
                record_dicts = [r.to_dict() for r in records]
                with open(self.training_file, "w") as f:
                    json.dump(record_dicts, f, indent=2)
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error deleting training record: {e}")
            return False
    
    def calculate_statistics(self):
        """Calculate basic statistics about shark pups."""
        pups = self.get_all_pups()
        if not pups:
            return {
                "count": 0,
                "live_count": 0,
                "stillborn_count": 0,
                "avg_length": 0,
                "avg_weight": 0,
                "min_length": 0,
                "max_length": 0,
                "min_weight": 0,
                "max_weight": 0,
                "mother_stats": {}
            }
        
        # Filter out None values for calculations
        lengths = [pup.length for pup in pups if pup.length is not None]
        weights = [pup.weight for pup in pups if pup.weight is not None]
        
        # Count live and stillborn pups
        live_pups = [pup for pup in pups if getattr(pup, 'status', 'live') == 'live']
        stillborn_pups = [pup for pup in pups if getattr(pup, 'status', 'live') == 'stillborn']
        
        # Group by mother shark
        mother_stats = {}
        for pup in pups:
            mother_id = getattr(pup, 'mother_id', 'Unknown')
            if not mother_id:
                mother_id = 'Unknown'
                
            if mother_id not in mother_stats:
                mother_stats[mother_id] = {
                    'total': 0,
                    'live': 0,
                    'stillborn': 0
                }
                
            mother_stats[mother_id]['total'] += 1
            
            # Count live/stillborn by mother
            if getattr(pup, 'status', 'live') == 'live':
                mother_stats[mother_id]['live'] += 1
            elif getattr(pup, 'status', 'live') == 'stillborn':
                mother_stats[mother_id]['stillborn'] += 1
        
        return {
            "count": len(pups),
            "live_count": len(live_pups),
            "stillborn_count": len(stillborn_pups),
            "avg_length": sum(lengths) / len(lengths) if lengths else 0,
            "avg_weight": sum(weights) / len(weights) if weights else 0,
            "min_length": min(lengths) if lengths else 0,
            "max_length": max(lengths) if lengths else 0,
            "min_weight": min(weights) if weights else 0,
            "max_weight": max(weights) if weights else 0,
            "mother_stats": mother_stats
        }
    
    def get_monthly_data(self):
        """Get data grouped by month for charting."""
        pups = self.get_all_pups()
        
        # Initialize monthly data
        monthly_data = {}
        
        for pup in pups:
            try:
                # Parse the date and extract the year-month
                date_obj = datetime.strptime(pup.date, "%Y-%m-%d")
                month_key = f"{date_obj.year}-{date_obj.month:02d}"
                
                # Initialize the month if it doesn't exist
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        "count": 0,
                        "total_length": 0,
                        "total_weight": 0
                    }
                
                # Update the month's data
                monthly_data[month_key]["count"] += 1
                monthly_data[month_key]["total_length"] += pup.length
                monthly_data[month_key]["total_weight"] += pup.weight
            except Exception as e:
                logging.error(f"Error processing pup date {pup.date}: {e}")
        
        # Calculate averages and format for Chart.js
        labels = []
        counts = []
        avg_lengths = []
        avg_weights = []
        
        # Sort by month
        for month in sorted(monthly_data.keys()):
            data = monthly_data[month]
            labels.append(month)
            counts.append(data["count"])
            avg_lengths.append(data["total_length"] / data["count"] if data["count"] > 0 else 0)
            avg_weights.append(data["total_weight"] / data["count"] if data["count"] > 0 else 0)
        
        return {
            "labels": labels,
            "counts": counts,
            "avg_lengths": avg_lengths,
            "avg_weights": avg_weights
        }
    
    def get_feeding_statistics(self, pup_id=None):
        """Calculate statistics about feeding records."""
        # Use feeding sessions instead of old feeding records
        if pup_id:
            sessions = self.get_feeding_sessions_by_pup_id(pup_id)
        else:
            sessions = self.get_all_feeding_sessions()
        
        if not sessions:
            return {
                "total_records": 0,
                "food_types": [],
                "food_type_data": {"labels": [], "values": []},
                "avg_amount": 0,
                "max_amount": 0,
                "min_amount": 0,
                "most_common_food": "None"
            }
        
        # Calculate statistics
        amounts = []
        food_type_amounts = {}
        total_records = 0
        
        # Process all sessions and food items
        for session in sessions:
            for food_item in session.food_items:
                # Add amount to list for overall statistics
                amount = food_item.amount
                amounts.append(amount)
                total_records += 1
                
                # Track food type consumption
                food_type = food_item.food_type
                if food_type in food_type_amounts:
                    food_type_amounts[food_type] += amount
                else:
                    food_type_amounts[food_type] = amount
        
        # Find most common food type by amount
        most_common_food = "None"
        max_food_amount = 0
        for food_type, amount in food_type_amounts.items():
            if amount > max_food_amount:
                max_food_amount = amount
                most_common_food = food_type
                
        # Format food type data for chart
        food_type_chart_data = {
            "labels": list(food_type_amounts.keys()),
            "values": list(food_type_amounts.values())
        }
        
        # Format food type data for display
        food_type_data = [{
            "name": food_type,
            "amount": amount
        } for food_type, amount in food_type_amounts.items()]
        
        # Return comprehensive statistics
        return {
            "total_records": total_records,
            "food_types": food_type_data,
            "food_type_data": food_type_chart_data,
            "avg_amount": sum(amounts) / len(amounts) if amounts else 0,
            "max_amount": max(amounts) if amounts else 0,
            "min_amount": min(amounts) if amounts else 0,
            "most_common_food": most_common_food
        }
    
    # Feeding Sessions Methods
    def get_all_feeding_sessions(self):
        """Get all feeding sessions from the feeding sessions file."""
        try:
            with open(self.feeding_sessions_file, "r") as f:
                session_dicts = json.load(f)
                return [FeedingSession.from_dict(session) for session in session_dicts]
        except Exception as e:
            logging.error(f"Error reading feeding sessions data: {e}")
            return []
    
    def get_feeding_sessions_by_pup_id(self, pup_id):
        """Get feeding sessions for a specific shark pup."""
        try:
            sessions = self.get_all_feeding_sessions()
            return [s for s in sessions if s.pup_id == pup_id]
        except Exception as e:
            logging.error(f"Error getting feeding sessions for pup ID {pup_id}: {e}")
            return []
    
    def add_feeding_session(self, session):
        """Add a new feeding session to the feeding sessions file."""
        try:
            sessions = self.get_all_feeding_sessions()
            
            # Set ID to be one more than the highest existing ID, or 1 if no sessions exist
            max_id = max([s.id or 0 for s in sessions], default=0) if sessions else 0
            session.id = max_id + 1
            
            session_dicts = [s.to_dict() for s in sessions]
            session_dicts.append(session.to_dict())
            
            with open(self.feeding_sessions_file, "w") as f:
                json.dump(session_dicts, f, indent=2)
            
            return session
        except Exception as e:
            logging.error(f"Error adding feeding session: {e}")
            return None
    
    def get_feeding_session_by_id(self, session_id):
        """Get a feeding session by ID."""
        try:
            sessions = self.get_all_feeding_sessions()
            for session in sessions:
                if session.id == session_id:
                    return session
            return None
        except Exception as e:
            logging.error(f"Error getting feeding session by ID: {e}")
            return None
            
    def update_feeding_session(self, session_id, updated_data):
        """Update an existing feeding session."""
        try:
            sessions = self.get_all_feeding_sessions()
            session_to_update = None
            
            # Find the session to update
            for i, session in enumerate(sessions):
                if session.id == session_id:
                    session_to_update = session
                    sessions.remove(session)
                    break
                    
            if not session_to_update:
                return None
                
            # Update basic session info
            if 'date' in updated_data:
                session_to_update.date = updated_data['date']
            if 'session_notes' in updated_data:
                session_to_update.session_notes = updated_data['session_notes']
            if 'feeding_time' in updated_data:
                session_to_update.feeding_time = updated_data['feeding_time']
            
            # Update food items if provided
            if 'food_items' in updated_data:
                session_to_update.food_items = []
                for item_data in updated_data['food_items']:
                    session_to_update.add_food_item(
                        food_type=item_data['food_type'],
                        amount=item_data['amount'],
                        notes=item_data.get('notes', '')
                    )
            
            # Add updated session back to the list
            sessions.append(session_to_update)
            
            # Save sessions
            session_dicts = [s.to_dict() for s in sessions]
            with open(self.feeding_sessions_file, "w") as f:
                json.dump(session_dicts, f, indent=2)
            
            return session_to_update
            
        except Exception as e:
            logging.error(f"Error updating feeding session: {e}")
            return None
            
    def delete_feeding_session(self, session_id):
        """Delete a feeding session."""
        try:
            sessions = self.get_all_feeding_sessions()
            original_count = len(sessions)
            
            # Filter out the session to delete
            sessions = [s for s in sessions if s.id != session_id]
            
            if len(sessions) < original_count:
                # Save the updated list
                session_dicts = [s.to_dict() for s in sessions]
                with open(self.feeding_sessions_file, "w") as f:
                    json.dump(session_dicts, f, indent=2)
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error deleting feeding session: {e}")
            return False
    
    def get_feeding_sessions_statistics(self, pup_id=None):
        """Calculate statistics about feeding sessions."""
        if pup_id:
            sessions = self.get_feeding_sessions_by_pup_id(pup_id)
        else:
            sessions = self.get_all_feeding_sessions()
        
        if not sessions:
            return {
                "count": 0,
                "food_types": [],
                "avg_items_per_session": 0,
                "total_amount": 0
            }
        
        # Calculate statistics
        food_types = {}
        total_amount = 0
        all_items_count = 0
        
        for session in sessions:
            for food_item in session.food_items:
                all_items_count += 1
                total_amount += food_item.amount
                
                if food_item.food_type in food_types:
                    food_types[food_item.food_type]["count"] += 1
                    food_types[food_item.food_type]["amount"] += food_item.amount
                else:
                    food_types[food_item.food_type] = {
                        "count": 1,
                        "amount": food_item.amount
                    }
        
        food_type_data = [{
            "name": food_type,
            "count": stats["count"],
            "amount": stats["amount"],
            "avg_amount": stats["amount"] / stats["count"]
        } for food_type, stats in food_types.items()]
        
        return {
            "count": len(sessions),
            "food_types": food_type_data,
            "avg_items_per_session": all_items_count / len(sessions) if sessions else 0,
            "total_amount": total_amount,
            "avg_amount_per_session": total_amount / len(sessions) if sessions else 0
        }
    
    def get_training_statistics(self, pup_id=None):
        """Calculate statistics about training records."""
        if pup_id:
            records = self.get_training_records_by_pup_id(pup_id)
        else:
            records = self.get_all_training_records()
        
        if not records:
            return {
                "count": 0,
                "training_types": [],
                "progress_breakdown": {},
                "avg_duration": 0
            }
        
        # Calculate statistics
        training_types = {}
        progress_breakdown = {}
        durations = [record.duration for record in records]
        
        for record in records:
            # Count by training type
            if record.training_type in training_types:
                training_types[record.training_type] += 1
            else:
                training_types[record.training_type] = 1
            
            # Count by progress status
            if record.progress in progress_breakdown:
                progress_breakdown[record.progress] += 1
            else:
                progress_breakdown[record.progress] = 1
        
        training_type_data = [{
            "name": training_type,
            "count": count
        } for training_type, count in training_types.items()]
        
        progress_data = [{
            "status": progress,
            "count": count
        } for progress, count in progress_breakdown.items()]
        
        return {
            "count": len(records),
            "training_types": training_type_data,
            "progress_breakdown": progress_data,
            "avg_duration": sum(durations) / len(durations) if durations else 0
        }
        
    # Measurement Records Methods
    def get_all_measurements(self):
        """Get all measurement records from the measurements file."""
        try:
            with open(self.measurements_file, "r") as f:
                data = json.load(f)
                measurements = []
                for item in data:
                    measurements.append(MeasurementRecord.from_dict(item))
                return measurements
        except (FileNotFoundError, json.JSONDecodeError):
            return []
            
    def get_measurements_by_pup_id(self, pup_id):
        """Get measurement records for a specific shark pup."""
        all_measurements = self.get_all_measurements()
        return [m for m in all_measurements if str(m.pup_id) == str(pup_id)]
        
    def add_measurement(self, measurement):
        """Add a new measurement record to the measurements file."""
        measurements = self.get_all_measurements()
        
        # Generate a unique ID if none exists
        if measurement.id is None:
            # Find the highest existing ID and add 1
            max_id = 0
            for m in measurements:
                if m.id and int(m.id) > max_id:
                    max_id = int(m.id)
            measurement.id = str(max_id + 1)
        
        measurements.append(measurement)
        
        with open(self.measurements_file, "w") as f:
            json.dump([m.to_dict() for m in measurements], f, indent=2)
        
        return measurement
        
    def get_measurement_by_id(self, measurement_id):
        """Get a measurement record by ID."""
        for measurement in self.get_all_measurements():
            if measurement.id == measurement_id:
                return measurement
        return None
        
    def update_measurement(self, measurement_id, updated_data):
        """Update an existing measurement record."""
        measurements = self.get_all_measurements()
        
        for i, measurement in enumerate(measurements):
            if measurement.id == measurement_id:
                # Update the measurement with new data
                for key, value in updated_data.items():
                    setattr(measurement, key, value)
                
                # Save all measurements back to file
                with open(self.measurements_file, "w") as f:
                    json.dump([m.to_dict() for m in measurements], f, indent=2)
                
                return measurement
                
        return None
        
    def delete_measurement(self, measurement_id):
        """Delete a measurement record."""
        measurements = self.get_all_measurements()
        
        for i, measurement in enumerate(measurements):
            if measurement.id == measurement_id:
                # Remove the measurement from the list
                del measurements[i]
                
                # Save all measurements back to file
                with open(self.measurements_file, "w") as f:
                    json.dump([m.to_dict() for m in measurements], f, indent=2)
                
                return True
                
        return False
        
    def get_growth_statistics(self, pup_id=None):
        """Calculate statistics about pup growth based on measurement records."""
        measurements = self.get_all_measurements()
        
        if pup_id:
            measurements = [m for m in measurements if m.pup_id == pup_id]
        
        # Default structure with None values for all stats
        stats = {
            "total_records": 0,
            "weight_stats": {
                "min": None,
                "max": None,
                "avg": None,
                "growth_rate": None
            },
            "length_stats": {
                "min": None,
                "max": None,
                "avg": None,
                "growth_rate": None
            }
        }
        
        if not measurements:
            return stats
        
        # Update total records
        stats["total_records"] = len(measurements)
        
        # Weight statistics
        weights = [m.weight for m in measurements if m.weight is not None]
        if weights:
            stats["weight_stats"]["min"] = min(weights)
            stats["weight_stats"]["max"] = max(weights)
            stats["weight_stats"]["avg"] = sum(weights) / len(weights)
            
            # Calculate growth rates if there are multiple measurements
            if len(weights) >= 2:
                try:
                    # Sort measurements by date
                    sorted_weight_measurements = sorted([m for m in measurements if m.weight is not None], 
                                                      key=lambda x: x.date)
                    
                    # Calculate total weight growth and time span
                    first_weight = sorted_weight_measurements[0].weight
                    last_weight = sorted_weight_measurements[-1].weight
                    
                    first_date = datetime.strptime(sorted_weight_measurements[0].date, "%Y-%m-%d")
                    last_date = datetime.strptime(sorted_weight_measurements[-1].date, "%Y-%m-%d")
                    
                    days_diff = (last_date - first_date).days
                    if days_diff > 0:
                        weight_growth_rate = (last_weight - first_weight) / days_diff  # g per day
                        stats["weight_stats"]["growth_rate"] = weight_growth_rate
                except Exception as e:
                    # Keep growth_rate as None if there's any error in calculation
                    pass
        
        # Length statistics
        lengths = [m.length for m in measurements if m.length is not None]
        if lengths:
            stats["length_stats"]["min"] = min(lengths)
            stats["length_stats"]["max"] = max(lengths)
            stats["length_stats"]["avg"] = sum(lengths) / len(lengths)
            
            # Calculate growth rates if there are multiple measurements
            if len(lengths) >= 2:
                try:
                    # Sort measurements by date
                    sorted_length_measurements = sorted([m for m in measurements if m.length is not None], 
                                                     key=lambda x: x.date)
                    
                    # Calculate total length growth and time span
                    first_length = sorted_length_measurements[0].length
                    last_length = sorted_length_measurements[-1].length
                    
                    first_date = datetime.strptime(sorted_length_measurements[0].date, "%Y-%m-%d")
                    last_date = datetime.strptime(sorted_length_measurements[-1].date, "%Y-%m-%d")
                    
                    days_diff = (last_date - first_date).days
                    if days_diff > 0:
                        length_growth_rate = (last_length - first_length) / days_diff  # cm per day
                        stats["length_stats"]["growth_rate"] = length_growth_rate
                except Exception as e:
                    # Keep growth_rate as None if there's any error in calculation
                    pass
        
        return stats

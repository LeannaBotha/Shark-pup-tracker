import logging
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, Response
from app import app, db
from flask_login import login_user, logout_user, login_required, current_user
from models import SharkPup, FeedingRecord, TrainingRecord, FeedingSession, FoodItem, MeasurementRecord, SharkPupUser
from data_manager import DataManager
import csv
from io import StringIO

# Initialize data manager
data_manager = DataManager()

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    # Check if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        # Find the user in the database
        user = SharkPupUser.query.filter_by(username=username).first()
        
        # Check if user exists and password is correct
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash('Login successful!', 'success')
            
            # Redirect to the page the user was trying to access
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    # Check if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if username is None or len(str(username)) < 4:
            flash('Username must be at least 4 characters long.', 'danger')
        elif password is None or len(str(password)) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match.', 'danger')
        else:
            # Check if username or email already exists
            existing_user = SharkPupUser.query.filter_by(username=username).first()
            existing_email = SharkPupUser.query.filter_by(email=email).first()
            
            if existing_user:
                flash('Username already exists. Please choose a different one.', 'danger')
            elif existing_email:
                flash('Email already registered. Please use a different email or log in.', 'danger')
            else:
                # Create new user
                new_user = SharkPupUser()
                new_user.username = username
                new_user.email = email
                new_user.set_password(password)
                
                db.session.add(new_user)
                db.session.commit()
                
                flash('Registration successful! You can now log in.', 'success')
                return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Redirect to history page after login since it's used more frequently."""
    return redirect(url_for('history'))

@app.route('/add')
@login_required
def add_new_pup():
    """Render the page for adding a new pup."""
    return render_template('index.html')

@app.route('/add_pup', methods=['POST'])
@login_required
def add_pup():
    """Add a new shark pup entry with researcher tracking."""
    try:
        # Get data from the form
        date = request.form.get('date')
        name = request.form.get('name')
        notes = request.form.get('notes', '')
        date_of_birth = request.form.get('date_of_birth', None)
        mother_id = request.form.get('mother_id', None)
        sex = request.form.get('sex', None)
        status = request.form.get('status', 'live')  # Default to 'live' if not specified
        
        # Get optional measurements
        length = request.form.get('length', None)
        weight = request.form.get('weight', None)
        
        # Convert empty strings to None for optional fields
        length = None if length == '' else length
        weight = None if weight == '' else weight
        date_of_birth = None if date_of_birth == '' else date_of_birth
        mother_id = None if mother_id == '' else mother_id
        sex = None if sex == '' else sex
        
        # Create new SharkPup object with researcher tracking and status
        pup = SharkPup(
            date=date, 
            name=name, 
            notes=notes, 
            length=length, 
            weight=weight, 
            date_of_birth=date_of_birth,
            mother_id=mother_id,
            sex=sex,
            researcher=current_user.username,
            status=status
        )
        
        # Save to database
        saved_pup = data_manager.add_pup(pup)
        
        if saved_pup:
            flash('Shark pup data saved successfully!', 'success')
        else:
            flash('Error saving shark pup data.', 'danger')
        
        return redirect(url_for('history'))
    
    except Exception as e:
        logging.error(f"Error adding shark pup: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/history')
@login_required
def history():
    """View the history of shark pup entries."""
    # Get query parameters for filtering
    sort_by = request.args.get('sort_by', 'date')
    order = request.args.get('order', 'desc')
    
    # Get all pups
    pups = data_manager.get_all_pups()
    
    # Apply sorting with safe handling of None values
    if sort_by == 'date':
        pups = sorted(pups, key=lambda x: x.date, reverse=(order == 'desc'))
    elif sort_by == 'name':
        pups = sorted(pups, key=lambda x: x.name, reverse=(order == 'desc'))
    elif sort_by == 'length':
        # Sort by length, placing None values at the end
        def length_key(x):
            if x.length is None:
                return float('inf') if order == 'asc' else float('-inf')
            return float(x.length)
        pups = sorted(pups, key=length_key, reverse=(order == 'desc'))
    elif sort_by == 'weight':
        # Sort by weight, placing None values at the end 
        def weight_key(x):
            if x.weight is None:
                return float('inf') if order == 'asc' else float('-inf')
            return float(x.weight)
        pups = sorted(pups, key=weight_key, reverse=(order == 'desc'))
    
    return render_template('history.html', pups=pups, sort_by=sort_by, order=order)

@app.route('/pup/<int:pup_id>')
@login_required
def pup_details(pup_id):
    """View details for a specific shark pup, including feeding and training records."""
    pup = data_manager.get_pup_by_id(pup_id)
    if not pup:
        flash('Shark pup not found.', 'danger')
        return redirect(url_for('history'))
    
    # Get both old feeding records and new feeding sessions
    feeding_records = data_manager.get_feeding_records_by_pup_id(pup_id)
    feeding_sessions = data_manager.get_feeding_sessions_by_pup_id(pup_id)
    training_records = data_manager.get_training_records_by_pup_id(pup_id)
    
    # Sort records by date (newest first)
    feeding_records = sorted(feeding_records, key=lambda x: x.date, reverse=True)
    feeding_sessions = sorted(feeding_sessions, key=lambda x: x.date, reverse=True) if feeding_sessions else []
    training_records = sorted(training_records, key=lambda x: x.date, reverse=True)
    
    # Get measurements for the pup
    measurements = data_manager.get_measurements_by_pup_id(pup_id)
    measurements = sorted(measurements, key=lambda x: x.date, reverse=True) if measurements else []
    
    # Calculate feeding statistics from sessions instead of old records
    feeding_stats = data_manager.get_feeding_statistics(pup_id)
    
    # Process feeding data for charts
    feeding_chart_data = {'dates': [], 'amounts': []}
    food_types_labels = []
    food_types_values = []
    food_type_totals = {}
    
    # Sort by date (oldest first for charts)
    chart_feeding_sessions = sorted(feeding_sessions, key=lambda x: x.date)
    
    # Calculate feeding amount per day for charts
    daily_feeding_data = {}
    
    # Process feeding sessions for chart data
    for session in chart_feeding_sessions:
        date = session.date
        
        # Add to daily feeding totals
        if date not in daily_feeding_data:
            daily_feeding_data[date] = 0
            
        # Add each food item to the total for this day
        for item in session.food_items:
            try:
                # Handle cases where amount might be None
                amount = item.amount or 0
                daily_feeding_data[date] += amount
                
                # Track food type totals for pie chart
                if item.food_type not in food_type_totals:
                    food_type_totals[item.food_type] = 0
                food_type_totals[item.food_type] += amount
            except Exception as e:
                # Use standard print for error reporting
                print(f"Error processing feeding data for date {date}: {e}")
                # Continue processing other items
    
    # Prepare date-sorted data for charts
    sorted_dates = sorted(daily_feeding_data.keys())
    feeding_chart_data['dates'] = sorted_dates
    feeding_chart_data['amounts'] = [daily_feeding_data[date] for date in sorted_dates]
    
    # Prepare food type data for pie chart
    food_types_labels = list(food_type_totals.keys())
    food_types_values = [food_type_totals[food_type] for food_type in food_types_labels]
    
    # Process notes for better display
    notes = pup.notes.split('\n') if pup.notes else []
    
    # Calculate measurement statistics if we have multiple measurements
    measurement_stats = {}
    if measurements and len(measurements) > 1:
        # Calculate growth over time
        oldest_measure = measurements[-1]  # Last measurement (oldest first)
        latest_measure = measurements[0]   # First measurement (newest first)
        
        if oldest_measure.weight is not None and latest_measure.weight is not None:
            weight_change = latest_measure.weight - oldest_measure.weight
            measurement_stats['weight_change'] = weight_change
            measurement_stats['weight_change_percent'] = (weight_change / oldest_measure.weight) * 100 if oldest_measure.weight else 0
        
        if oldest_measure.length is not None and latest_measure.length is not None:
            length_change = latest_measure.length - oldest_measure.length
            measurement_stats['length_change'] = length_change
            measurement_stats['length_change_percent'] = (length_change / oldest_measure.length) * 100 if oldest_measure.length else 0
    try:
        import json
        with open('shark_pups.json', 'r') as f:
            pup_data = json.load(f)
            for p in pup_data:
                if p['id'] == pup_id:
                    # Make sure notes are correctly passed to the template
                    notes = p.get('notes', '')
                    # Force notes to be a string
                    if notes is None:
                        notes = ''
                    break
    except Exception as e:
        import logging
        logging.error(f"Error reading pup notes: {e}")
    
    # Get measurement statistics
    measurement_stats = {}
    if measurements:
        measurement_stats = {
            'latest_weight': measurements[0].weight if measurements[0].weight is not None else "Not recorded",
            'latest_length': measurements[0].length if measurements[0].length is not None else "Not recorded",
            'latest_date': measurements[0].date
        }
        
        # If more than one measurement, calculate growth
        if len(measurements) > 1:
            oldest_measure = measurements[-1]
            if oldest_measure.weight is not None and measurements[0].weight is not None:
                weight_change = measurements[0].weight - oldest_measure.weight
                measurement_stats['weight_change'] = weight_change
                measurement_stats['weight_change_percent'] = (weight_change / oldest_measure.weight) * 100 if oldest_measure.weight else 0
            
            if oldest_measure.length is not None and measurements[0].length is not None:
                length_change = measurements[0].length - oldest_measure.length
                measurement_stats['length_change'] = length_change
                measurement_stats['length_change_percent'] = (length_change / oldest_measure.length) * 100 if oldest_measure.length else 0
    
    return render_template('pup_details.html', 
                          pup=pup, 
                          pup_notes=notes,
                          feeding_records=feeding_records,
                          feeding_sessions=feeding_sessions,
                          training_records=training_records,
                          measurements=measurements,
                          feeding_chart_data=feeding_chart_data,
                          food_types_labels=food_types_labels,
                          food_types_values=food_types_values,
                          measurement_stats=measurement_stats)

@app.route('/pup/<int:pup_id>/edit')
@login_required
def edit_pup(pup_id):
    """Show form to edit a shark pup's information."""
    pup = data_manager.get_pup_by_id(pup_id)
    if not pup:
        flash('Shark pup not found.', 'danger')
        return redirect(url_for('history'))
    
    return render_template('edit_pup.html', pup=pup)

@app.route('/pup/<int:pup_id>/update', methods=['POST'])
@login_required
def update_pup(pup_id):
    """Update a shark pup's information."""
    try:
        pup = data_manager.get_pup_by_id(pup_id)
        if not pup:
            flash('Shark pup not found.', 'danger')
            return redirect(url_for('history'))
        
        # Get form data with researcher tracking
        updated_data = {
            'date': request.form.get('date'),
            'name': request.form.get('name'),
            'notes': request.form.get('notes', ''),
            'date_of_birth': request.form.get('date_of_birth', ''),
            'mother_id': request.form.get('mother_id', ''),
            'sex': request.form.get('sex', ''),
            'length': request.form.get('length', ''),
            'weight': request.form.get('weight', ''),
            'status': request.form.get('status', 'live'),  # Track if pup is live or stillborn
            'researcher': current_user.username,  # Track who made the update
        }
        
        # Update the pup
        updated_pup = data_manager.update_pup(pup_id, updated_data)
        
        if updated_pup:
            flash('Shark pup data updated successfully!', 'success')
        else:
            flash('Error updating shark pup data.', 'danger')
        
        return redirect(url_for('pup_details', pup_id=pup_id))
    
    except Exception as e:
        logging.error(f"Error updating shark pup: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('edit_pup', pup_id=pup_id))

@app.route('/feeding', methods=['GET', 'POST'])
@login_required
def feeding():
    """Add or view feeding records."""
    if request.method == 'POST':
        try:
            # Get basic session info
            pup_id = int(request.form.get('pup_id', 0))
            date = request.form.get('date')
            session_notes = request.form.get('session_notes', '')
            feeding_time = request.form.get('feeding_time', 'AM')  # Get AM/PM feeding time
            
            # Create new FeedingSession object with researcher tracking
            session = FeedingSession(
                pup_id=pup_id, 
                date=date, 
                session_notes=session_notes,
                feeding_time=feeding_time,
                researcher=current_user.username  # Track who created the session
            )
            
            # Process food items from form
            food_types = request.form.getlist('food_type[]')
            amounts = request.form.getlist('amount[]')
            item_notes = request.form.getlist('item_notes[]')
            
            # Add each food item to the session
            for i in range(len(food_types)):
                if food_types[i] and amounts[i]:  # Skip empty entries
                    note = item_notes[i] if i < len(item_notes) else ""
                    session.add_food_item(
                        food_type=food_types[i],
                        amount=amounts[i],
                        notes=note
                    )
            
            # Save the session
            if session.food_items:  # Only save if there are food items
                saved_session = data_manager.add_feeding_session(session)
                
                if saved_session:
                    flash('Feeding session with multiple food items saved successfully!', 'success')
                else:
                    flash('Error saving feeding session.', 'danger')
                
                return redirect(url_for('pup_details', pup_id=pup_id))
            else:
                flash('Please add at least one food item to the feeding session.', 'warning')
        
        except Exception as e:
            logging.error(f"Error adding feeding session: {e}")
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('feeding'))
    
    # GET request - display the form
    pups = data_manager.get_all_pups()
    return render_template('feeding_session.html', pups=pups)

@app.route('/feeding/edit/<int:session_id>', methods=['GET', 'POST'])
@login_required
def edit_feeding_session(session_id):
    """Edit an existing feeding session."""
    session = data_manager.get_feeding_session_by_id(session_id)
    if not session:
        flash('Feeding session not found.', 'danger')
        return redirect(url_for('history'))
    
    if request.method == 'POST':
        try:
            # Get basic session info
            date = request.form.get('date')
            session_notes = request.form.get('session_notes', '')
            feeding_time = request.form.get('feeding_time', 'AM')
            
            # Process food items from form
            food_types = request.form.getlist('food_type[]')
            amounts = request.form.getlist('amount[]')
            item_notes = request.form.getlist('item_notes[]')
            
            # Create food items list
            food_items = []
            for i in range(len(food_types)):
                if food_types[i] and amounts[i]:  # Skip empty entries
                    note = item_notes[i] if i < len(item_notes) else ""
                    food_items.append({
                        'food_type': food_types[i],
                        'amount': amounts[i],
                        'notes': note
                    })
            
            # Update the session
            updated_data = {
                'date': date,
                'session_notes': session_notes,
                'feeding_time': feeding_time,
                'food_items': food_items
            }
            
            if food_items:  # Only update if there are food items
                updated_session = data_manager.update_feeding_session(session_id, updated_data)
                
                if updated_session:
                    flash('Feeding session updated successfully!', 'success')
                else:
                    flash('Error updating feeding session.', 'danger')
                
                return redirect(url_for('pup_details', pup_id=session.pup_id))
            else:
                flash('Please add at least one food item to the feeding session.', 'warning')
        
        except Exception as e:
            logging.error(f"Error updating feeding session: {e}")
            flash(f'Error: {str(e)}', 'danger')
    
    # GET request - display the form with existing data
    pups = data_manager.get_all_pups()
    pup = data_manager.get_pup_by_id(session.pup_id)
    
    return render_template('edit_feeding_session.html', 
                          session=session, 
                          pups=pups,
                          current_pup=pup)

@app.route('/feeding/delete/<int:session_id>', methods=['POST'])
@login_required
def delete_feeding_session(session_id):
    """Delete a feeding session."""
    session = data_manager.get_feeding_session_by_id(session_id)
    if not session:
        flash('Feeding session not found.', 'danger')
        return redirect(url_for('history'))
    
    pup_id = session.pup_id
    
    if data_manager.delete_feeding_session(session_id):
        flash('Feeding session deleted successfully!', 'success')
    else:
        flash('Error deleting feeding session.', 'danger')
    
    return redirect(url_for('pup_details', pup_id=pup_id))

@app.route('/training', methods=['GET', 'POST'])
@login_required
def training():
    """Add or view training records."""
    if request.method == 'POST':
        try:
            pup_id = int(request.form.get('pup_id', 0))
            date = request.form.get('date')
            training_type = request.form.get('training_type')
            duration = request.form.get('duration')
            progress = request.form.get('progress')
            notes = request.form.get('notes', '')
            
            # Create new TrainingRecord object with researcher tracking
            record = TrainingRecord(
                pup_id=pup_id, 
                date=date, 
                training_type=training_type, 
                duration=duration, 
                progress=progress, 
                notes=notes,
                researcher=current_user.username  # Track who created the training record
            )
            
            # Save to database
            saved_record = data_manager.add_training_record(record)
            
            if saved_record:
                flash('Training record saved successfully!', 'success')
            else:
                flash('Error saving training record.', 'danger')
            
            return redirect(url_for('pup_details', pup_id=pup_id))
        
        except Exception as e:
            logging.error(f"Error adding training record: {e}")
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('training'))
    
    # GET request - display the form
    pups = data_manager.get_all_pups()
    return render_template('training.html', pups=pups)

@app.route('/training/edit/<int:record_id>', methods=['GET', 'POST'])
@login_required
def edit_training_record(record_id):
    """Edit an existing training record."""
    record = data_manager.get_training_record_by_id(record_id)
    if not record:
        flash('Training record not found.', 'danger')
        return redirect(url_for('history'))
    
    if request.method == 'POST':
        try:
            # Get updated data from form
            date = request.form.get('date')
            training_type = request.form.get('training_type')
            duration = request.form.get('duration')
            progress = request.form.get('progress')
            notes = request.form.get('notes', '')
            
            # Update the record
            updated_data = {
                'date': date,
                'training_type': training_type,
                'duration': duration,
                'progress': progress,
                'notes': notes
            }
            
            updated_record = data_manager.update_training_record(record_id, updated_data)
            
            if updated_record:
                flash('Training record updated successfully!', 'success')
            else:
                flash('Error updating training record.', 'danger')
            
            return redirect(url_for('pup_details', pup_id=record.pup_id))
        
        except Exception as e:
            logging.error(f"Error updating training record: {e}")
            flash(f'Error: {str(e)}', 'danger')
    
    # GET request - display the form with existing data
    pups = data_manager.get_all_pups()
    pup = data_manager.get_pup_by_id(record.pup_id)
    
    return render_template('edit_training.html', 
                          record=record, 
                          pups=pups,
                          current_pup=pup)

@app.route('/training/delete/<int:record_id>', methods=['POST'])
def delete_training_record(record_id):
    """Delete a training record."""
    record = data_manager.get_training_record_by_id(record_id)
    if not record:
        flash('Training record not found.', 'danger')
        return redirect(url_for('history'))
    
    pup_id = record.pup_id
    
    if data_manager.delete_training_record(record_id):
        flash('Training record deleted successfully!', 'success')
    else:
        flash('Error deleting training record.', 'danger')
    
    return redirect(url_for('pup_details', pup_id=pup_id))

@app.route('/statistics')
def statistics():
    """View statistics about shark pups."""
    stats = data_manager.calculate_statistics()
    monthly_data = data_manager.get_monthly_data()
    
    # Get feeding and training statistics
    feeding_stats = data_manager.get_feeding_statistics()
    training_stats = data_manager.get_training_statistics()
    
    return render_template('statistics.html', 
                          stats=stats, 
                          monthly_data=monthly_data,
                          feeding_stats=feeding_stats,
                          training_stats=training_stats)

@app.route('/help')
def help():
    """View the help page."""
    return render_template('help.html')

@app.route('/api/pups', methods=['GET'])
def api_pups():
    """API endpoint to get all pups as JSON."""
    pups = data_manager.get_all_pups()
    return jsonify([pup.to_dict() for pup in pups])

@app.route('/api/feeding_records', methods=['GET'])
def api_feeding_records():
    """API endpoint to get feeding records as JSON."""
    pup_id = request.args.get('pup_id')
    if pup_id:
        records = data_manager.get_feeding_records_by_pup_id(int(pup_id))
    else:
        records = data_manager.get_all_feeding_records()
    return jsonify([record.to_dict() for record in records])

@app.route('/api/training_records', methods=['GET'])
def api_training_records():
    """API endpoint to get training records as JSON."""
    pup_id = request.args.get('pup_id')
    if pup_id:
        records = data_manager.get_training_records_by_pup_id(int(pup_id))
    else:
        records = data_manager.get_all_training_records()
    return jsonify([record.to_dict() for record in records])

@app.route('/api/statistics', methods=['GET'])
def api_statistics():
    """API endpoint to get statistics as JSON."""
    stats = data_manager.calculate_statistics()
    monthly_data = data_manager.get_monthly_data()
    feeding_stats = data_manager.get_feeding_statistics()
    training_stats = data_manager.get_training_statistics()
    
    return jsonify({
        "pup_stats": stats,
        "monthly_data": monthly_data,
        "feeding_stats": feeding_stats,
        "training_stats": training_stats
    })
    
# Export routes for data download
@app.route('/export')
def export_page():
    """Display the export options page."""
    pups = data_manager.get_all_pups()
    return render_template('export.html', pups=pups)

@app.route('/export/pups.csv')
def export_pups_csv():
    """Export all shark pups data as CSV."""
    pups = data_manager.get_all_pups()
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Name', 'Date Added', 'Date of Birth', 'Sex', 'Mother ID', 'Notes'])
    
    # Write data
    for pup in pups:
        writer.writerow([
            pup.id,
            pup.name,
            pup.date,
            pup.date_of_birth if hasattr(pup, 'date_of_birth') else '',
            pup.sex if hasattr(pup, 'sex') else '',
            pup.mother_id if hasattr(pup, 'mother_id') else '',
            pup.notes if hasattr(pup, 'notes') else ''
        ])
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=shark_pups.csv"}
    )

@app.route('/export/feeding_sessions.csv')
def export_feeding_sessions_csv():
    """Export all feeding sessions data as CSV."""
    sessions = data_manager.get_all_feeding_sessions()
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Session ID', 'Pup ID', 'Pup Name', 'Date', 'Time of Day', 'Food Type', 'Amount (g)', 'Notes'])
    
    # Write data
    for session in sessions:
        # Get pup name
        pup = data_manager.get_pup_by_id(session.pup_id)
        pup_name = pup.name if pup else ''
        
        # Export each food item as a separate row
        for item in session.food_items:
            writer.writerow([
                session.id,
                session.pup_id,
                pup_name,
                session.date,
                session.feeding_time,
                item.food_type,
                item.amount,
                f"{item.notes or ''} {session.session_notes or ''}".strip()
            ])
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=feeding_sessions.csv"}
    )

@app.route('/export/training.csv')
def export_training_csv():
    """Export all training records as CSV."""
    records = data_manager.get_all_training_records()
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Record ID', 'Pup ID', 'Pup Name', 'Date', 'Training Type', 'Duration (min)', 'Progress', 'Notes'])
    
    # Write data
    for record in records:
        # Get pup name
        pup = data_manager.get_pup_by_id(record.pup_id)
        pup_name = pup.name if pup else ''
        
        writer.writerow([
            record.id,
            record.pup_id,
            pup_name,
            record.date,
            record.training_type,
            record.duration,
            record.progress,
            record.notes or ''
        ])
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=training_records.csv"}
    )

@app.route('/export/measurements.csv')
def export_measurements_csv():
    """Export all measurement records as CSV."""
    measurements = data_manager.get_all_measurements()
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Measurement ID', 'Pup ID', 'Pup Name', 'Date', 'Weight (g)', 'Length (cm)', 'Notes'])
    
    # Write data
    for measurement in measurements:
        # Get pup name
        pup = data_manager.get_pup_by_id(measurement.pup_id)
        pup_name = pup.name if pup else ''
        
        writer.writerow([
            measurement.id,
            measurement.pup_id,
            pup_name,
            measurement.date,
            measurement.weight or '',
            measurement.length or '',
            measurement.notes or ''
        ])
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=measurements.csv"}
    )

@app.route('/export/pup/<pup_id>.csv')
def export_pup_data_csv(pup_id):
    """Export all data for a specific shark pup as CSV."""
    # Get pup info
    pup = data_manager.get_pup_by_id(pup_id)
    if not pup:
        flash('Shark pup not found.', 'danger')
        return redirect(url_for('export_page'))
    
    # Get all data for this pup
    feeding_records = data_manager.get_feeding_records_by_pup_id(pup_id)  # Get legacy feeding records
    feeding_sessions = data_manager.get_feeding_sessions_by_pup_id(pup_id)
    training_records = data_manager.get_training_records_by_pup_id(pup_id)
    measurements = data_manager.get_measurements_by_pup_id(pup_id)
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write pup information
    writer.writerow(['SHARK PUP INFORMATION'])
    writer.writerow(['ID', 'Name', 'Date Added', 'Date of Birth', 'Sex', 'Mother ID', 'Notes'])
    writer.writerow([
        pup.id,
        pup.name,
        pup.date,
        pup.date_of_birth if hasattr(pup, 'date_of_birth') else '',
        pup.sex if hasattr(pup, 'sex') else '',
        pup.mother_id if hasattr(pup, 'mother_id') else '',
        pup.notes if hasattr(pup, 'notes') else ''
    ])
    writer.writerow([])  # Empty row as separator
    
    # Write measurement information
    writer.writerow(['MEASUREMENTS'])
    writer.writerow(['Date', 'Weight (g)', 'Length (cm)', 'Notes'])
    for measurement in measurements:
        writer.writerow([
            measurement.date,
            measurement.weight or '',
            measurement.length or '',
            measurement.notes or ''
        ])
    writer.writerow([])  # Empty row as separator
    
    # Write feeding sessions (newer format)
    writer.writerow(['FEEDING SESSIONS'])
    writer.writerow(['Date', 'Time of Day', 'Food Type', 'Amount (g)', 'Notes', 'Researcher'])
    for session in feeding_sessions:
        for item in session.food_items:
            writer.writerow([
                session.date,
                session.feeding_time,
                item.food_type,
                item.amount,
                f"{item.notes or ''} {session.session_notes or ''}".strip(),
                session.researcher or ''
            ])
    
    # Write legacy feeding records if any exist
    if feeding_records:
        writer.writerow([])  # Empty row as separator
        writer.writerow(['LEGACY FEEDING RECORDS'])
        writer.writerow(['Date', 'Food Type', 'Amount (g)', 'Notes', 'Researcher'])
        for record in feeding_records:
            writer.writerow([
                record.date,
                record.food_type,
                record.amount,
                record.notes or '',
                getattr(record, 'researcher', '') or ''
            ])
    writer.writerow([])  # Empty row as separator
    
    # Write training records
    writer.writerow(['TRAINING RECORDS'])
    writer.writerow(['Date', 'Training Type', 'Duration (min)', 'Progress', 'Notes'])
    for record in training_records:
        writer.writerow([
            record.date,
            record.training_type,
            record.duration,
            record.progress,
            record.notes or ''
        ])
    
    filename = f"shark_pup_{pup.name.replace(' ', '_')}.csv"
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )
    
@app.route('/measurements/<int:pup_id>', methods=['GET', 'POST'])
def measurements(pup_id):
    """Add or view measurement records for a specific pup."""
    pup = data_manager.get_pup_by_id(str(pup_id))
    if not pup:
        flash("Shark pup not found.", "danger")
        return redirect(url_for('history'))
        
    if request.method == 'POST':
        # Add a new measurement
        date = request.form.get('date')
        weight = request.form.get('weight')
        length = request.form.get('length')
        notes = request.form.get('notes')
        
        # Make sure at least one measurement is provided
        if (weight == '' or weight is None) and (length == '' or length is None):
            flash("Please provide at least one measurement (weight or length).", "warning")
            return redirect(url_for('measurements', pup_id=pup_id))
            
        # Convert empty strings to None
        weight = float(weight) if weight and weight != '' else None
        length = float(length) if length and length != '' else None
        
        # Create and save measurement record
        measurement = MeasurementRecord(
            pup_id=pup_id,
            date=date,
            weight=weight,
            length=length,
            notes=notes
        )
        
        data_manager.add_measurement(measurement)
        flash("Measurement record added successfully!", "success")
        return redirect(url_for('measurements', pup_id=pup_id))
    
    # GET request
    all_measurements = data_manager.get_measurements_by_pup_id(pup_id)
    measurements_by_date = {}
    
    # Group measurements by date for display
    for m in all_measurements:
        if m.date in measurements_by_date:
            measurements_by_date[m.date].append(m)
        else:
            measurements_by_date[m.date] = [m]
    
    # Sort by date (newest first)
    sorted_dates = sorted(measurements_by_date.keys(), reverse=True)
    sorted_measurements = [(date, measurements_by_date[date]) for date in sorted_dates]
    
    # Calculate growth statistics for this pup
    growth_stats = data_manager.get_growth_statistics(pup_id)
    
    return render_template(
        'measurements.html',
        pup=pup,
        measurements=all_measurements,
        sorted_measurements=sorted_measurements,
        growth_stats=growth_stats,
        today=datetime.now().strftime('%Y-%m-%d')
    )
    
@app.route('/edit_measurement/<measurement_id>', methods=['GET', 'POST'])
def edit_measurement(measurement_id):
    """Edit an existing measurement record."""
    measurement = data_manager.get_measurement_by_id(measurement_id)
    if not measurement:
        flash("Measurement record not found.", "danger")
        return redirect(url_for('history'))
    
    pup = data_manager.get_pup_by_id(measurement.pup_id)
    
    if request.method == 'POST':
        # Update the measurement
        date = request.form.get('date')
        weight = request.form.get('weight')
        length = request.form.get('length')
        notes = request.form.get('notes')
        
        # Make sure at least one measurement is provided
        if (weight == '' or weight is None) and (length == '' or length is None):
            flash("Please provide at least one measurement (weight or length).", "warning")
            return redirect(url_for('edit_measurement', measurement_id=measurement_id))
            
        # Convert empty strings to None
        weight = float(weight) if weight and weight != '' else None
        length = float(length) if length and length != '' else None
        
        # Update measurement record
        updated_data = {
            'date': date,
            'weight': weight,
            'length': length,
            'notes': notes
        }
        
        data_manager.update_measurement(measurement_id, updated_data)
        flash("Measurement record updated successfully!", "success")
        return redirect(url_for('measurements', pup_id=measurement.pup_id))
    
    # GET request
    return render_template(
        'edit_measurement.html',
        measurement=measurement,
        pup=pup
    )
    
@app.route('/delete_measurement/<measurement_id>', methods=['POST'])
def delete_measurement(measurement_id):
    """Delete a measurement record."""
    measurement = data_manager.get_measurement_by_id(measurement_id)
    if not measurement:
        flash("Measurement record not found.", "danger")
        return redirect(url_for('history'))
        
    pup_id = measurement.pup_id
    
    if data_manager.delete_measurement(measurement_id):
        flash("Measurement record deleted successfully!", "success")
    else:
        flash("Failed to delete measurement record.", "danger")
        
    return redirect(url_for('measurements', pup_id=pup_id))
    
@app.route('/feeding_graph/<int:pup_id>')
def feeding_graph(pup_id):
    """View a graph of feeding data for a specific pup."""
    pup = data_manager.get_pup_by_id(str(pup_id))
    if not pup:
        flash("Shark pup not found.", "danger")
        return redirect(url_for('history'))
    
    # Get feeding sessions for this pup
    feeding_sessions = data_manager.get_feeding_sessions_by_pup_id(pup_id)
    
    # Process data for the chart
    feeding_dates = []
    daily_amounts = []
    food_type_counts = {}
    
    # Calculate feeding amount per day
    daily_feeding_data = {}
    
    for session in feeding_sessions:
        date = session.date
        if date not in daily_feeding_data:
            daily_feeding_data[date] = 0
        
        # Add up all food items in this session
        session_amount = 0
        for item in session.food_items:
            session_amount += item.amount
            
            # Count food types for the pie chart
            if item.food_type in food_type_counts:
                food_type_counts[item.food_type] += item.amount
            else:
                food_type_counts[item.food_type] = item.amount
                
        daily_feeding_data[date] += session_amount
    
    # Sort dates for the graph
    sorted_dates = sorted(daily_feeding_data.keys())
    
    for date in sorted_dates:
        feeding_dates.append(date)
        daily_amounts.append(daily_feeding_data[date])
    
    # Prepare the data for the charts
    feeding_data = {
        'dates': feeding_dates if feeding_dates else [],
        'amounts': daily_amounts if daily_amounts else []
    }
    
    # Make sure we have values for the food types chart - convert to list directly
    food_types_labels = list(food_type_counts.keys()) if food_type_counts else []
    food_types_values = list(food_type_counts.values()) if food_type_counts else []
    
    # Calculate feeding statistics
    feeding_stats = None
    if daily_amounts:
        feeding_stats = {
            'total_records': len(feeding_sessions),
            'avg_daily_amount': sum(daily_amounts) / len(daily_amounts),
            'max_daily_amount': max(daily_amounts),
            'min_daily_amount': min(daily_amounts)
        }
        
    return render_template(
        'feeding_graph.html',
        pup=pup,
        feeding_data=feeding_data,
        food_types_labels=food_types_labels,
        food_types_values=food_types_values,
        feeding_stats=feeding_stats,
        feeding_records=sorted(feeding_sessions, key=lambda x: x.date, reverse=True)
    )


@app.route('/feeding/comparison')
def feeding_comparison():
    """Compare feeding data across all live pups."""
    all_pups = data_manager.get_all_pups()
    
    # Filter only live pups
    live_pups = [pup for pup in all_pups if getattr(pup, 'status', 'live') == 'live']
    
    if not live_pups:
        flash("No live pups found in the database", "warning")
        return redirect(url_for('history'))
    
    # Collect all food types across all pups
    all_food_types = set()
    pup_stats = {}
    
    # Process each pup's feeding data
    for pup in live_pups:
        # Get feeding sessions for this pup
        sessions = data_manager.get_feeding_sessions_by_pup_id(pup.id)
        
        # Initialize stats for this pup
        pup_stats[pup.id] = {
            'total_amount': 0,
            'session_count': len(sessions),
            'food_types': {},
            'preferred_food': None
        }
        
        # Process feeding data
        for session in sessions:
            for food_item in session.food_items:
                all_food_types.add(food_item.food_type)
                
                if food_item.food_type not in pup_stats[pup.id]['food_types']:
                    pup_stats[pup.id]['food_types'][food_item.food_type] = 0
                
                pup_stats[pup.id]['food_types'][food_item.food_type] += food_item.amount
                pup_stats[pup.id]['total_amount'] += food_item.amount
        
        # Determine preferred food (most consumed)
        if pup_stats[pup.id]['food_types']:
            pup_stats[pup.id]['preferred_food'] = max(
                pup_stats[pup.id]['food_types'].items(), 
                key=lambda x: x[1]
            )[0]
    
    # Convert to list for easier sorting
    all_food_types = sorted(list(all_food_types))
    
    # Prepare data for the combined feeding chart
    chart_colors = [
        {'bg': 'rgba(255, 99, 132, 0.7)', 'border': 'rgba(255, 99, 132, 1)'},
        {'bg': 'rgba(54, 162, 235, 0.7)', 'border': 'rgba(54, 162, 235, 1)'},
        {'bg': 'rgba(255, 206, 86, 0.7)', 'border': 'rgba(255, 206, 86, 1)'},
        {'bg': 'rgba(75, 192, 192, 0.7)', 'border': 'rgba(75, 192, 192, 1)'},
        {'bg': 'rgba(153, 102, 255, 0.7)', 'border': 'rgba(153, 102, 255, 1)'}
    ]
    
    # Prepare datasets for the combined feeding chart
    combined_datasets = []
    for i, pup in enumerate(live_pups):
        dataset = {
            'label': pup.name,
            'data': [],
            'backgroundColor': chart_colors[i % len(chart_colors)]['bg'],
            'borderColor': chart_colors[i % len(chart_colors)]['border'],
            'borderWidth': 1
        }
        
        # Add data for each food type
        for food_type in all_food_types:
            amount = pup_stats[pup.id]['food_types'].get(food_type, 0)
            dataset['data'].append(amount)
        
        combined_datasets.append(dataset)
    
    combined_feeding_data = {
        'foodTypes': all_food_types,
        'datasets': combined_datasets
    }
    
    # Prepare data for the diet preference chart
    diet_preference_data = {
        'pupNames': [pup.name for pup in live_pups],
        'preferredFoods': [pup_stats[pup.id]['preferred_food'] for pup in live_pups],
        'preferenceValues': [1 for _ in live_pups]  # Just for visualization, each pup has equal weight
    }
    
    return render_template(
        'feeding_comparison.html', 
        pups=all_pups,
        pup_stats=pup_stats,
        combined_feeding_data=combined_feeding_data,
        diet_preference_data=diet_preference_data
    )

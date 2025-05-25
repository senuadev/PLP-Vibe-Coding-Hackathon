from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from utils.gemini_utils import init_gemini, process_audio_transaction, process_image_transaction
from sqlalchemy.orm import relationship

# Configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///expense_tracker.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Initialize Flask extensions
db = SQLAlchemy()
login_manager = LoginManager()

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    # Relationships
    receipts = relationship('Receipt', back_populates='user', cascade='all, delete-orphan')
    categories = relationship('Category', back_populates='user', cascade='all, delete-orphan')


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='categories')
    receipts = relationship('Receipt', back_populates='category')
    
    def __repr__(self):
        return f'<Category {self.name}>'


class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    transaction_type = db.Column(db.Enum('income', 'expense', name='transaction_type_enum'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    
    # Relationships
    user = relationship('User', back_populates='receipts')
    category = relationship('Category', back_populates='receipts')
    
    def __repr__(self):
        return f'<Receipt {self.amount} {self.transaction_type} ({self.created_at})>'

def create_app(config_class=Config):
    # Load environment variables
    load_dotenv("secrets.env")

    # Initialize Gemini
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY not found in environment variables")

    try:
        gemini_model = init_gemini(GEMINI_API_KEY) if GEMINI_API_KEY else None
    except Exception as e:
        print(f"Warning: Failed to initialize Gemini: {str(e)}")
        gemini_model = None

    # Create and configure the app
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    # Create database tables
    with app.app_context():
        db.create_all()

    # Register blueprints (for future use)
    # from app.auth import bp as auth_bp
    # app.register_blueprint(auth_bp, url_prefix='/auth')

    # Authentication routes
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            if not all([username, email, password]):
                flash('All fields are required', 'danger')
                return redirect(url_for('register'))
                
            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'danger')
                return redirect(url_for('register'))
                
            if User.query.filter_by(email=email).first():
                flash('Email already registered', 'danger')
                return redirect(url_for('register'))
                
            user = User(username=username, email=email)
            user.set_password(password)
            
            db.session.add(user)
            db.session.flush()  # Get the user ID
            
            # Create default categories for the new user
            default_categories = [
                {'name': 'Food & Dining', 'description': 'Restaurants, groceries, coffee shops'},
                {'name': 'Shopping', 'description': 'Clothing, electronics, other purchases'},
                {'name': 'Housing', 'description': 'Rent, mortgage, utilities'},
                {'name': 'Transportation', 'description': 'Gas, public transit, car maintenance'},
                {'name': 'Income', 'description': 'Salary, bonuses, other income'},
                {'name': 'Entertainment', 'description': 'Movies, games, hobbies'},
                {'name': 'Health', 'description': 'Medical expenses, insurance'},
                {'name': 'Other', 'description': 'Miscellaneous expenses'}
            ]
            
            for cat_data in default_categories:
                category = Category(
                    name=cat_data['name'],
                    description=cat_data['description'],
                    user_id=user.id
                )
                db.session.add(category)
            
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        if request.method == 'POST':
            identifier = request.form.get('identifier')  # Can be username or email
            password = request.form.get('password')
            remember = True if request.form.get('remember') else False
            
            user = User.query.filter(
                (User.username == identifier) | (User.email == identifier)
            ).first()
            
            if user and user.check_password(password):
                login_user(user, remember=remember)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
                
            flash('Invalid username/email or password', 'danger')
            
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))

    # Simple routes
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Calculate totals
        totals = {
            'income': db.session.query(
                db.func.sum(Receipt.amount)
            ).filter(
                Receipt.user_id == current_user.id,
                Receipt.transaction_type == 'income'
            ).scalar() or 0,
            'expense': db.session.query(
                db.func.sum(Receipt.amount)
            ).filter(
                Receipt.user_id == current_user.id,
                Receipt.transaction_type == 'expense'
            ).scalar() or 0
        }
        
        # Get recent transactions
        recent_transactions = Receipt.query.filter_by(user_id=current_user.id)\
            .order_by(Receipt.created_at.desc())\
            .limit(5).all()
        
        # Get categories summary
        categories_summary = db.session.query(
            Category.name,
            db.func.sum(Receipt.amount).label('total')
        ).join(
            Receipt, Category.id == Receipt.category_id
        ).filter(
            Receipt.user_id == current_user.id,
            Receipt.transaction_type == 'expense'
        ).group_by(
            Category.name
        ).all()
        
        # Calculate percentages for each category
        total_expenses = totals['expense']
        if total_expenses > 0:
            categories_summary = [{
                'name': cat.name,
                'total': float(cat.total),
                'percentage': (float(cat.total) / total_expenses) * 100
            } for cat in categories_summary]
        else:
            categories_summary = []
        
        return render_template(
            'dashboard.html',
            totals=totals,
            recent_transactions=recent_transactions,
            categories_summary=categories_summary
        )
        
    @app.route('/receipts')
    @login_required
    def view_receipts():
        page = request.args.get('page', 1, type=int)
        filter_type = request.args.get('filter', 'all')
        per_page = 10
        
        # Base query
        query = Receipt.query.filter_by(user_id=current_user.id)
        
        # Apply filter if specified
        if filter_type == 'income':
            query = query.filter_by(transaction_type='income')
        elif filter_type == 'expense':
            query = query.filter_by(transaction_type='expense')
        
        # Get paginated results
        receipts = query.order_by(Receipt.created_at.desc())\
                      .paginate(page=page, per_page=per_page, error_out=False)
        
        # Calculate totals
        totals = {
            'income': db.session.query(
                db.func.sum(Receipt.amount)
            ).filter(
                Receipt.user_id == current_user.id,
                Receipt.transaction_type == 'income'
            ).scalar() or 0,
            'expense': db.session.query(
                db.func.sum(Receipt.amount)
            ).filter(
                Receipt.user_id == current_user.id,
                Receipt.transaction_type == 'expense'
            ).scalar() or 0
        }
        
        return render_template('view_receipts.html', 
                             receipts=receipts, 
                             totals=totals,
                             current_filter=filter_type)
        
    @app.route('/receipts/create', methods=['GET', 'POST'])
    @login_required
    def create_receipt():
        # Get transaction type from URL parameter if present
        transaction_type = request.args.get('transaction_type')
        
        if request.method == 'POST':
            amount = request.form.get('amount')
            description = request.form.get('description', '').strip()
            transaction_type = request.form.get('transaction_type')
            category_id = request.form.get('category_id')
            
            # Validate required fields
            if not all([amount, transaction_type]):
                flash('Amount and transaction type are required', 'danger')
                return redirect(url_for('create_receipt'))
                
            try:
                amount = float(amount)
                if amount <= 0:
                    raise ValueError("Amount must be positive")
            except (ValueError, TypeError):
                flash('Please enter a valid amount', 'danger')
                return redirect(url_for('create_receipt'))
                
            # Validate category belongs to user if provided
            category = None
            if category_id:
                category = Category.query.filter_by(
                    id=category_id, 
                    user_id=current_user.id
                ).first()
                if not category:
                    flash('Invalid category', 'danger')
                    return redirect(url_for('create_receipt'))
            
            receipt = Receipt(
                amount=amount,
                description=description,
                transaction_type=transaction_type,
                user_id=current_user.id,
                category_id=category.id if category else None
            )
            
            db.session.add(receipt)
            db.session.commit()
            
            flash('Transaction added successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('view_receipts'))
            
        # Get user's categories for the form
        categories = Category.query.filter_by(user_id=current_user.id).all()
        return render_template(
            'create_receipt.html', 
            categories=categories,
            transaction_type=transaction_type
        )
    
    @app.route('/voice_input')
    @login_required
    def voice_input():
        # Get user's categories for the form
        categories = Category.query.filter_by(user_id=current_user.id).all()
        return render_template('voice_input.html', categories=categories)

    @app.route('/image_input')
    @login_required
    def image_input():
        # Get user's categories for the form
        categories = Category.query.filter_by(user_id=current_user.id).all()
        return render_template('image_input.html', categories=categories)
        
    @app.route('/process_image', methods=['POST'])
    @login_required
    def process_image():
        """Process image file to extract transaction details using Gemini."""
        # Check if the post request has the file part
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            }), 400
            
        file = request.files['image']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No selected file'
            }), 400
            
        if not gemini_model:
            return jsonify({
                'success': False,
                'error': 'Gemini API not properly configured'
            }), 500
            
        try:
            # Process the image file with Gemini
            transaction_data = process_image_transaction(file, gemini_model)
            
            # Add user ID to the transaction data
            transaction_data['user_id'] = current_user.id
            
            # Return the extracted transaction data
            return jsonify({
                'success': True,
                'transaction': transaction_data
            })
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error processing image: {str(e)}'
            }), 500
            
    @app.route('/process_audio', methods=['POST'])
    @login_required
    def process_audio():
        """Process audio file to extract transaction details using Gemini."""
        # Check if the post request has the file part
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio file provided'
            }), 400
            
        file = request.files['audio']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No selected file'
            }), 400
            
        if not gemini_model:
            return jsonify({
                'success': False,
                'error': 'Gemini API not properly configured'
            }), 500
            
        try:
            # Process the audio file with Gemini
            filename = file.filename if hasattr(file, 'filename') else 'recording.wav'
            transaction_data = process_audio_transaction(file, gemini_model, filename=filename)
            
            # Add user ID to the transaction data
            transaction_data['user_id'] = current_user.id
            
            # Return the extracted transaction data
            return jsonify({
                'success': True,
                'transaction': transaction_data
            })
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error processing audio: {str(e)}'
            }), 500
    
    @app.route('/save_transaction', methods=['POST'])
    @login_required
    def save_transaction():
        """Save transaction data to the database."""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No data provided'
                }), 400
                
            # Validate required fields
            required_fields = ['amount', 'transaction_type', 'description']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400
            
            # Create new receipt
            receipt = Receipt(
                amount=float(data['amount']),
                description=data['description'],
                transaction_type=data['transaction_type'],
                user_id=current_user.id,
                category_id=data.get('category_id'),
                created_at=datetime.strptime(data.get('transaction_date'), '%Y-%m-%d') if data.get('transaction_date') else datetime.utcnow()
            )
            
            db.session.add(receipt)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Transaction saved successfully',
                'receipt_id': receipt.id
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': f'Error saving transaction: {str(e)}'
            }), 500
    
    return app

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

# Create upload folder for voice recordings
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed extensions for audio files
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'flac', 'aiff'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    app = create_app()
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.run(debug=True)

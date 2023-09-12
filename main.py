import os
from datetime import date

import boto3
import sendgrid
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, configure_uploads, IMAGES
from sendgrid.helpers.mail import Mail

load_dotenv()  # Load variables from .env file

app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///features.db'  # SQLite database file name
db = SQLAlchemy(app)

# Replace 'YOUR_SENDGRID_API_KEY' with your actual SendGrid API key
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
print(SENDGRID_API_KEY)
sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

# Flask-Uploads configuration
photos = UploadSet("photos", IMAGES)
app.config["UPLOADED_PHOTOS_DEST"] = "uploads"  # Specify the folder to store uploaded files
configure_uploads(app, photos)

# AWS S3 configuration
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)

# Define the Feature model with many-to-many relationships
owners = db.Table('owners',
                  db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                  db.Column('feature_id', db.Integer, db.ForeignKey('feature.id'))
                  )

contributors = db.Table('contributors',
                        db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                        db.Column('feature_id', db.Integer, db.ForeignKey('feature.id'))
                        )

feature_tag_association = db.Table(
    'feature_tag_association',
    db.Column('feature_id', db.Integer, db.ForeignKey('feature.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'))
)


class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    features = db.relationship('Feature', secondary='feature_tag_association', back_populates='tags')


class User(db.Model):
    """
    Basic username storage so we can filter by user.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)


# Define the Feature model
class Feature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    video_url = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(50), nullable=True)
    owners = db.relationship('User', secondary=owners, backref=db.backref('owners', lazy='dynamic'))
    contributors = db.relationship('User', secondary=contributors,
                                   backref=db.backref('contributors', lazy='dynamic'))
    tags = db.relationship('Tag', secondary='feature_tag_association', back_populates='features')
    date = db.Column(db.String(10), nullable=True)


# Create the database tables (only once, typically in a separate script)
with app.app_context():
    db.create_all()


@app.route('/')
def index():
    """
    Root route to take to add Feature
    :return:
    """
    features = Feature.query.all()
    categories = [feature.category for feature in features if feature.category]
    categories = list(set(categories))  # Remove duplicates
    return render_template('index.html', features=features, categories=categories)


@app.route('/add_feature', methods=['POST'])
def add_feature():
    # Check if an image file was uploaded
    s3_url = None
    if 'image' in request.files:
        image = request.files['image']
        if image.filename != '':
            # Generate a unique filename for the image (e.g., using UUID)
            new_filename = "example.jpg"

            # # Save the image to a temporary location
            # temp_image_path = os.path.join(app.config['UPLOADS_DEFAULT_DEST'], new_filename)
            # image.save(temp_image_path)

            # Upload the image to Amazon S3
            s3_client.put_object(
                Body=image,
                Bucket=S3_BUCKET_NAME,
                Key=image.filename,
            )

            s3_url = "https://lvreleasenotes.s3.ap-south-1.amazonaws.com/{0}".format(image.filename)

    feature_name = request.form.get('name')
    feature_description = request.form.get('description')
    video_url = request.form.get('video_url')
    category = request.form.get('category')
    date = request.form.get('date')

    # Create a new Feature instance and add it to the database
    new_feature = Feature(
        name=feature_name,
        description=feature_description,
        image_url=s3_url,
        video_url=video_url,
        category=category,
        date=date
    )

    # Add owners and contributors
    owner_names = request.form.getlist('owners')  # Get owner names from the form
    if request.form['contributors'] == '':
        contributor_names = []
    else:
        contributor_names = request.form.getlist('contributors')  # Get contributor names from the form

    owners = []
    contributors = []

    # Create owner and contributor objects and associate them with the feature
    for owner_name in owner_names:
        owner = User.query.filter_by(name=owner_name).first()
        if owner:
            owners.append(owner)
        else:
            owner = User(name=owner_name)
            db.session.add(owner)

            owners.append(owner)

    for contributor_name in contributor_names:
        contributor = User.query.filter_by(name=contributor_name).first()
        if contributor:
            contributors.append(contributor)
        else:
            contributor = User(name=contributor_name)
            db.session.add(contributor)
            contributors.append(contributor)

    new_feature.owners = owners
    new_feature.contributors = contributors

    tags_input = request.form.get('tags')
    # Split the tags input into a list
    tags = [tag.strip() for tag in tags_input.split(',')]

    # Associate tags with the feature
    for tag_name in tags:
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
        new_feature.tags.append(tag)

    db.session.add(new_feature)
    db.session.commit()

    return redirect(url_for('index'))


@app.route('/all_features')
def all_features():
    features = Feature.query.all()
    categories = [feature.category for feature in features if feature.category]
    categories = list(set(categories))  # Remove duplicates
    return render_template('all_features.html', features=features, categories=categories)


@app.route('/send_email', methods=['POST'])
def send_email():
    # selected_features = request.form.getlist('selected_features')
    features = Feature.query.all()

    # Get the last two selected features
    # last_two_features = selected_features[-1:]

    # Generate HTML email content based on selected features
    email_content = render_template('feature_email.html', selected_features=features)

    # Create a SendGrid Mail object
    message = Mail(
        from_email='ishaan.sutaria@letsventure.com',  # Replace with your sender email
        to_emails='ishaansutaria@gmail.com',  # Replace with your recipient email
        subject="LetsVenture Release Notes: Date {0}".format(date.today().strftime('%d-%m-%Y')),
        html_content=email_content
    )

    # Send the email using SendGrid
    try:
        response = sg.send(message)
        return 'Email sent successfully'
    except Exception as e:
        return f'Error sending email: {str(e)}'


@app.route('/delete_feature', methods=['DELETE'])
def delete_feature():
    # Get the feature name to delete from the request JSON
    data = request.get_json()
    feature_name = data.get("name")

    feature_to_delete = Feature.query.filter_by(name=feature_name).first()

    if feature_to_delete:
        db.session.delete(feature_to_delete)
        db.session.commit()
        return jsonify({"message": f"Feature '{feature_name}' deleted successfully"}), 200
    else:
        return jsonify({"message": f"Feature '{feature_name}' not found"}), 404


@app.route('/get_tag_suggestions', methods=['GET'])
def get_tag_suggestions():
    query = request.args.get('query').strip()

    # Query your database or other data source for tag suggestions
    # In this example, we use a list of hardcoded tag suggestions
    tag_suggestions = ['Tag1', 'Tag2', 'Tag3']

    # Filter suggestions based on the user's input
    suggestions = [tag for tag in tag_suggestions if query.lower() in tag.lower()]

    return jsonify(suggestions)


if __name__ == '__main__':
    app.run(debug=True)

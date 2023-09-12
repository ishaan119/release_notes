# Release Notes

## Overview

In this feature, we are enhancing our minimalistic release notes project to provide the following capabilities:

1. **Add New Feature:** Users can add a new feature to the release notes. Each feature consists of a name, description,
   category, date, and optional image and video URL.

2. **Send Email:** Users have the option to select one or more features and send them via email. The selected features
   will be included in the email content.

3. **View Feature List:** Users can view the list of features in the project. Features are categorized, and users can
   filter them by category.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Installation

Provide instructions on how to install and set up your Flask project. Include any dependencies that need to be
installed.

```bash
# Clone the repository
git clone https://github.com/yourusername/your-repo.git

# Navigate to the project directory
cd your-repo

# Create a virtual environment (optional but recommended)
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```shell
$ flask run
```

## Configuration option 1

```dotenv
export SECRET_KEY=mysecretkey

# Configuration option 2
export DATABASE_URL=postgresql://username:password@localhost/mydatabase
```
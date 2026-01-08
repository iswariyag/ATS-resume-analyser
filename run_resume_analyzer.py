# run_resume_analyzer.py
import subprocess
import sys
import os

def check_install_dependencies():
    """Check and install required dependencies if needed."""
    print("Checking and installing required dependencies...")
    
    required_packages = [
        "streamlit",
        "pandas",
        "matplotlib",
        "seaborn",
        "plotly",
        "spacy",
        "scikit-learn",
        "python-dateutil",
        "PyMuPDF"
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} is already installed")
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ {package} installed successfully")
    
    # Check if spacy model is installed
    try:
        import spacy
        spacy.load("en_core_web_sm")
        print("✓ Spacy English model is already installed")
    except OSError:
        print("Installing Spacy English language model...")
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        print("✓ Spacy English model installed successfully")

def run_app():
    """Run the Streamlit app."""
    print("\nStarting Resume Analyzer application...")
    
    # Check if app.py exists in the current directory
    if not os.path.exists("app.py"):
        print("Error: app.py not found in the current directory.")
        return False
    
    # Check if other required files exist
    required_files = ["resume_parser.py", "job_matcher.py"]
    for file in required_files:
        if not os.path.exists(file):
            print(f"Error: {file} not found in the current directory.")
            return False
    
    # Run the Streamlit app
    try:
        subprocess.run(["streamlit", "run", "app.py"])
        return True
    except Exception as e:
        print(f"Error running the application: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("        RESUME ANALYZER APPLICATION SETUP AND LAUNCHER        ")
    print("=" * 60)
    
    # Check and install dependencies
    check_install_dependencies()
    
    # Run the app
    success = run_app()
    
    if not success:
        print("\nThere was an issue starting the application.")
        print("Make sure all required files (app.py, resume_parser.py, job_matcher.py) are in the current directory.")
        print("\nAlternatively, you can start the application manually with:")
        print("streamlit run app.py")
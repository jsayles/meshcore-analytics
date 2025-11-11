import subprocess
import sys


def web():
    """Run Django development server"""
    subprocess.run([sys.executable, "./manage.py", "runserver"])


def tests():
    """Run Django tests in parallel"""
    subprocess.run([sys.executable, "./manage.py", "test", "--parallel", "auto"])


def review():
    """Check for outdated packages"""
    subprocess.run([sys.executable, "-m", "pip", "list", "--outdated"])

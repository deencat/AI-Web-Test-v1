"""
Pytest configuration for integration tests
Disables output capturing for real-time logging
"""
import pytest
import sys
import os

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'

# Configure pytest to show output immediately
def pytest_configure(config):
    """Configure pytest for real-time output"""
    # Try to disable output capturing if not already disabled
    # Note: This may not work if -s is not used, but we try anyway
    if hasattr(config.option, 'capture'):
        # If capture is set to 'no', output is already not captured
        if config.option.capture != 'no':
            # Try to set capture to 'no' programmatically
            # This is a best-effort attempt
            try:
                config.option.capture = 'no'
            except:
                pass

def pytest_collection_modifyitems(config, items):
    """Modify test items to disable capture for slow tests"""
    for item in items:
        # For tests marked as 'slow', try to disable capture
        if 'slow' in item.keywords:
            # Add a marker to indicate we want real-time output
            # The actual disabling happens via -s flag
            pass


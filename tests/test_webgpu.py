import pytest
import subprocess
import time
import sys
from playwright.sync_api import Page, expect

@pytest.fixture(scope="module")
def http_server():
    """Start a simple HTTP server in the background."""
    # Start server on port 8080 to avoid conflict
    proc = subprocess.Popen([sys.executable, "-m", "http.server", "8080"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1) # Give it a moment to bind
    yield
    proc.terminate()
    proc.wait()

def test_webgpu_no_console_errors(page: Page, http_server):
    """
    Load the WebGPU page and ensure no console errors or warnings appear.
    Requires a browser with WebGPU support (Chromium).
    """
    errors = []

    def handle_console(msg):
        if msg.type in ["error", "warning"]:
            # Filter out harmless favicon 404s if any
            if "favicon" in msg.text:
                return
            # Filter out non-fatal info
            errors.append(f"[{msg.type}] {msg.text}")

    page.on("console", handle_console)
    
    # Navigate to the page
    page.goto("http://localhost:8080/index.html")
    
    # Wait for a few frames to render (approx 1 second)
    page.wait_for_timeout(1000)
    
    # Check if we caught any errors
    if errors:
        pytest.fail(f"Console errors detected:\n" + "\n".join(errors))
    
    # Optional: Check if the canvas exists and has WebGPU context
    # (Hard to verify context strictly without deeper introspection, but absence of errors is the main check)
    canvas = page.locator("#gpuCanvas")
    expect(canvas).to_be_visible()

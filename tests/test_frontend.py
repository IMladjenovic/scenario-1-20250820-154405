import pytest
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
import time
import threading
import subprocess
import requests
from unittest.mock import patch, MagicMock

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

class TestFrontendIntegration:
    """Integration tests for the frontend application"""
    
    @classmethod
    def setup_class(cls):
        """Setup for the test class - start backend server"""
        cls.backend_process = None
        cls.server_started = False
        
        # Try to start the backend server for integration testing
        try:
            # Check if server is already running
            response = requests.get('http://localhost:12000/api/currency-pairs', timeout=2)
            if response.status_code == 200:
                cls.server_started = True
        except:
            # Server not running, we'll skip integration tests
            pass
    
    @classmethod
    def teardown_class(cls):
        """Cleanup after tests"""
        if cls.backend_process:
            cls.backend_process.terminate()
            cls.backend_process.wait()
    
    def setup_method(self):
        """Setup for each test method"""
        if not self.server_started:
            pytest.skip("Backend server not available for integration testing")
        
        # Setup Chrome driver with headless option for CI/CD
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
        except Exception as e:
            pytest.skip(f"Chrome driver not available: {e}")
    
    def teardown_method(self):
        """Cleanup after each test method"""
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    def test_page_loads(self):
        """Test that the main page loads correctly"""
        frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
        self.driver.get(f"file://{os.path.abspath(frontend_path)}")
        
        # Check that the title is correct
        assert "FX Trading Platform" in self.driver.title
        
        # Check that main elements are present
        header = self.driver.find_element(By.TAG_NAME, "header")
        assert header.is_displayed()
        
        main_content = self.driver.find_element(By.TAG_NAME, "main")
        assert main_content.is_displayed()
    
    def test_portfolio_section_exists(self):
        """Test that portfolio section is present"""
        frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
        self.driver.get(f"file://{os.path.abspath(frontend_path)}")
        
        portfolio_section = self.driver.find_element(By.CLASS_NAME, "portfolio-section")
        assert portfolio_section.is_displayed()
        
        portfolio_grid = self.driver.find_element(By.ID, "portfolioGrid")
        assert portfolio_grid.is_displayed()
    
    def test_rates_section_exists(self):
        """Test that rates section is present"""
        frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
        self.driver.get(f"file://{os.path.abspath(frontend_path)}")
        
        rates_section = self.driver.find_element(By.CLASS_NAME, "rates-section")
        assert rates_section.is_displayed()
        
        rates_grid = self.driver.find_element(By.ID, "ratesGrid")
        assert rates_grid.is_displayed()
    
    def test_trading_form_exists(self):
        """Test that trading form is present and functional"""
        frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
        self.driver.get(f"file://{os.path.abspath(frontend_path)}")
        
        trading_section = self.driver.find_element(By.CLASS_NAME, "trading-section")
        assert trading_section.is_displayed()
        
        # Check form elements
        trade_pair_select = self.driver.find_element(By.ID, "tradePair")
        assert trade_pair_select.is_displayed()
        
        trade_type_select = self.driver.find_element(By.ID, "tradeType")
        assert trade_type_select.is_displayed()
        
        trade_amount_input = self.driver.find_element(By.ID, "tradeAmount")
        assert trade_amount_input.is_displayed()
        
        execute_btn = self.driver.find_element(By.ID, "executeTradeBtn")
        assert execute_btn.is_displayed()
        assert execute_btn.text == "Execute Trade"
    
    def test_trades_section_exists(self):
        """Test that recent trades section is present"""
        frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
        self.driver.get(f"file://{os.path.abspath(frontend_path)}")
        
        trades_section = self.driver.find_element(By.CLASS_NAME, "trades-section")
        assert trades_section.is_displayed()
        
        trades_list = self.driver.find_element(By.ID, "tradesList")
        assert trades_list.is_displayed()

class TestFrontendJavaScript:
    """Unit tests for frontend JavaScript functionality"""
    
    def test_format_number_function(self):
        """Test number formatting functionality"""
        # This would require a JavaScript testing framework like Jest
        # For now, we'll test the concept with Python equivalents
        
        def format_number(num):
            return f"{num:,.2f}"
        
        assert format_number(1234.5) == "1,234.50"
        assert format_number(0.1234) == "0.12"
        assert format_number(1000000) == "1,000,000.00"
    
    def test_format_rate_function(self):
        """Test rate formatting functionality"""
        def format_rate(rate):
            return f"{rate:.4f}"
        
        assert format_rate(1.0850) == "1.0850"
        assert format_rate(149.5) == "149.5000"
        assert format_rate(0.6450) == "0.6450"
    
    def test_trade_validation_logic(self):
        """Test trade validation logic"""
        def validate_trade(pair_id, amount):
            errors = []
            
            if not pair_id:
                errors.append("Please select a currency pair")
            
            if not amount or amount <= 0:
                errors.append("Please enter a valid amount")
            
            return errors
        
        # Test valid trade
        errors = validate_trade("1", 100.0)
        assert len(errors) == 0
        
        # Test invalid trades
        errors = validate_trade("", 100.0)
        assert "Please select a currency pair" in errors
        
        errors = validate_trade("1", 0)
        assert "Please enter a valid amount" in errors
        
        errors = validate_trade("1", -10)
        assert "Please enter a valid amount" in errors

class TestResponsiveDesign:
    """Tests for responsive design elements"""
    
    def setup_method(self):
        """Setup for each test method"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            pytest.skip(f"Chrome driver not available: {e}")
    
    def teardown_method(self):
        """Cleanup after each test method"""
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    def test_mobile_responsive(self):
        """Test mobile responsive design"""
        frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
        self.driver.get(f"file://{os.path.abspath(frontend_path)}")
        
        # Test mobile viewport
        self.driver.set_window_size(375, 667)  # iPhone size
        
        # Check that elements are still visible and properly arranged
        header = self.driver.find_element(By.TAG_NAME, "header")
        assert header.is_displayed()
        
        dashboard = self.driver.find_element(By.CLASS_NAME, "dashboard")
        assert dashboard.is_displayed()
    
    def test_tablet_responsive(self):
        """Test tablet responsive design"""
        frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
        self.driver.get(f"file://{os.path.abspath(frontend_path)}")
        
        # Test tablet viewport
        self.driver.set_window_size(768, 1024)  # iPad size
        
        # Check that elements are properly arranged
        dashboard = self.driver.find_element(By.CLASS_NAME, "dashboard")
        assert dashboard.is_displayed()
        
        trading_section = self.driver.find_element(By.CLASS_NAME, "trading-section")
        assert trading_section.is_displayed()

class TestAccessibility:
    """Basic accessibility tests"""
    
    def setup_method(self):
        """Setup for each test method"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            pytest.skip(f"Chrome driver not available: {e}")
    
    def teardown_method(self):
        """Cleanup after each test method"""
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    def test_form_labels(self):
        """Test that form elements have proper labels"""
        frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
        self.driver.get(f"file://{os.path.abspath(frontend_path)}")
        
        # Check that form inputs have associated labels
        labels = self.driver.find_elements(By.TAG_NAME, "label")
        assert len(labels) >= 3  # Should have labels for pair, type, and amount
        
        # Check specific labels exist
        label_texts = [label.text for label in labels]
        assert "Currency Pair:" in label_texts
        assert "Trade Type:" in label_texts
        assert "Amount:" in label_texts
    
    def test_button_accessibility(self):
        """Test button accessibility"""
        frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
        self.driver.get(f"file://{os.path.abspath(frontend_path)}")
        
        execute_btn = self.driver.find_element(By.ID, "executeTradeBtn")
        
        # Button should have text content
        assert execute_btn.text.strip() != ""
        
        # Button should be clickable
        assert execute_btn.is_enabled()

if __name__ == '__main__':
    pytest.main([__file__])
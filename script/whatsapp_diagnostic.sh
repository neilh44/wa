#!/usr/bin/env python3
"""
WhatsApp API Error Diagnosis Script
This script helps diagnose 422 Unprocessable Entity errors when making POST requests
to the WhatsApp API session endpoint.
"""

import requests
import json
import logging
import sys
from typing import Dict, Any, Optional, List, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("whatsapp_error_diagnosis")

class WhatsAppErrorDiagnoser:
    """Diagnoses WhatsApp API errors by testing various request configurations."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        """
        Initialize the diagnoser with the API base URL.
        
        Args:
            base_url: The base URL of the WhatsApp API
        """
        self.base_url = base_url
        self.session_endpoint = f"{base_url}/api/whatsapp/session"
        # Common request headers
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def test_basic_request(self) -> Tuple[int, Dict[str, Any]]:
        """
        Test a basic session creation request with minimal required fields.
        
        Returns:
            Tuple of (status_code, response_json)
        """
        # Minimal payload based on common WhatsApp API requirements
        payload = {
            "phone_number": "1234567890",  # Replace with actual test number
            "session_id": "test_session"   # Unique session identifier
        }
        
        logger.info(f"Testing basic request with payload: {payload}")
        response = requests.post(
            self.session_endpoint,
            headers=self.headers,
            json=payload
        )
        
        status_code = response.status_code
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            response_json = {"error": "Could not decode JSON response"}
            
        return status_code, response_json
    
    def test_common_field_variations(self) -> List[Dict[str, Any]]:
        """
        Test various field combinations to identify which fields might be causing validation errors.
        
        Returns:
            List of test results with payload variations and their responses
        """
        test_results = []
        
        # Common field variations for WhatsApp session creation
        variations = [
            # Test with device ID
            {
                "phone_number": "1234567890",
                "session_id": "test_session",
                "device_id": "test_device_001"
            },
            # Test with authentication token
            {
                "phone_number": "1234567890",
                "session_id": "test_session",
                "auth_token": "test_auth_token_123"
            },
            # Test with webhook URL
            {
                "phone_number": "1234567890",
                "session_id": "test_session",
                "webhook_url": "https://example.com/webhook"
            },
            # Test with full phone number format including country code
            {
                "phone_number": "+11234567890",
                "session_id": "test_session"
            }
        ]
        
        for payload in variations:
            logger.info(f"Testing variation with payload: {payload}")
            response = requests.post(
                self.session_endpoint,
                headers=self.headers,
                json=payload
            )
            
            try:
                response_json = response.json()
            except json.JSONDecodeError:
                response_json = {"error": "Could not decode JSON response"}
                
            test_results.append({
                "payload": payload,
                "status_code": response.status_code,
                "response": response_json
            })
        
        return test_results
    
    def inspect_api_schema(self) -> Dict[str, Any]:
        """
        Attempt to retrieve API schema or documentation endpoints to understand required fields.
        
        Returns:
            API schema if available, otherwise error information
        """
        # Common endpoints where schema might be available
        schema_endpoints = [
            f"{self.base_url}/api/docs",
            f"{self.base_url}/api/schema",
            f"{self.base_url}/api/swagger",
            f"{self.base_url}/api/openapi.json"
        ]
        
        for endpoint in schema_endpoints:
            logger.info(f"Attempting to access schema at: {endpoint}")
            try:
                response = requests.get(endpoint)
                if response.status_code == 200:
                    try:
                        return {"endpoint": endpoint, "schema": response.json()}
                    except json.JSONDecodeError:
                        # Might be HTML docs
                        return {
                            "endpoint": endpoint, 
                            "content_type": response.headers.get("Content-Type"),
                            "found": True
                        }
            except requests.RequestException as e:
                logger.error(f"Error accessing {endpoint}: {str(e)}")
        
        return {"error": "Could not find API schema information"}
    
    def test_with_request_logs(self) -> Dict[str, Any]:
        """
        Make a request with detailed logging of the request/response cycle.
        
        Returns:
            Dictionary with request and response details
        """
        payload = {
            "phone_number": "1234567890",
            "session_id": "test_session"
        }
        
        logger.info(f"Making request with detailed logging: {payload}")
        
        # Create a session to capture request details
        session = requests.Session()
        prepared_request = requests.Request(
            "POST",
            self.session_endpoint,
            headers=self.headers,
            json=payload
        ).prepare()
        
        # Log request details
        logger.info(f"Request URL: {prepared_request.url}")
        logger.info(f"Request method: {prepared_request.method}")
        logger.info(f"Request headers: {prepared_request.headers}")
        logger.info(f"Request body: {prepared_request.body}")
        
        # Send the request
        response = session.send(prepared_request)
        
        # Log response details
        result = {
            "request": {
                "url": prepared_request.url,
                "method": prepared_request.method,
                "headers": dict(prepared_request.headers),
                "body": prepared_request.body.decode('utf-8') if prepared_request.body else None
            },
            "response": {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text
            }
        }
        
        return result

    def run_diagnostics(self) -> Dict[str, Any]:
        """
        Run all diagnostic tests and aggregate results.
        
        Returns:
            Dictionary with all test results
        """
        diagnostics = {}
        
        # Run basic request test
        status_code, response = self.test_basic_request()
        diagnostics["basic_request"] = {
            "status_code": status_code,
            "response": response
        }
        
        # Run field variation tests
        diagnostics["field_variations"] = self.test_common_field_variations()
        
        # Attempt to retrieve API schema
        diagnostics["api_schema"] = self.inspect_api_schema()
        
        # Run detailed request logging
        diagnostics["detailed_request"] = self.test_with_request_logs()
        
        # Analyze results and provide recommendations
        diagnostics["analysis"] = self._analyze_results(diagnostics)
        
        return diagnostics
    
    def _analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze diagnostic results and provide recommendations.
        
        Args:
            results: The diagnostic test results
            
        Returns:
            Analysis and recommendations
        """
        analysis = {
            "possible_issues": [],
            "recommendations": []
        }
        
        # Check if any requests succeeded
        any_success = False
        for variation in results.get("field_variations", []):
            if variation.get("status_code") == 200:
                any_success = True
                analysis["working_payload"] = variation.get("payload")
                break
        
        # Basic request analysis
        basic_request = results.get("basic_request", {})
        if basic_request.get("status_code") == 422:
            response_body = basic_request.get("response", {})
            
            # Look for validation error details
            if "detail" in response_body:
                analysis["validation_errors"] = response_body["detail"]
                
                # Add specific issues based on validation errors
                if isinstance(response_body["detail"], list):
                    for error in response_body["detail"]:
                        if "loc" in error and "msg" in error:
                            field = ".".join(str(item) for item in error["loc"])
                            issue = f"Field '{field}': {error['msg']}"
                            analysis["possible_issues"].append(issue)
                            
                            # Add specific recommendation
                            if "required" in error["msg"].lower():
                                analysis["recommendations"].append(
                                    f"Add the required field '{field}' to your request payload"
                                )
                            elif "not a valid" in error["msg"].lower():
                                analysis["recommendations"].append(
                                    f"Fix the format of field '{field}' in your request payload"
                                )
        
        # Add general recommendations if no specific ones were found
        if not analysis["recommendations"]:
            if not any_success:
                analysis["recommendations"].extend([
                    "Check the API documentation for required fields",
                    "Ensure your authentication credentials are correct",
                    "Verify the format of phone numbers (try with/without country code)",
                    "Check if the session_id needs to follow a specific format"
                ])
        
        return analysis

def main():
    """Main function to run the diagnostic script."""
    # Get custom base URL from command line if provided
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    
    logger.info(f"Starting WhatsApp API error diagnosis with base URL: {base_url}")
    diagnoser = WhatsAppErrorDiagnoser(base_url)
    
    # Run diagnostics
    results = diagnoser.run_diagnostics()
    
    # Output results
    logger.info("Diagnostic Results:")
    logger.info(json.dumps(results["analysis"], indent=2))
    
    # Save full results to file
    with open("whatsapp_api_diagnostics.json", "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info("Full diagnostic results saved to whatsapp_api_diagnostics.json")

if __name__ == "__main__":
    main()
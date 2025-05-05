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
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000", port: int = None):
        """
        Initialize the diagnoser with the API base URL and optional port.
        
        Args:
            base_url: The base URL of the WhatsApp API
            port: Optional port to override the one in base_url
        """
        self.base_url = base_url
        
        # Override port if specified
        if port:
            if "://" in base_url:
                protocol, rest = base_url.split("://", 1)
                if "/" in rest:
                    host, path = rest.split("/", 1)
                    if ":" in host:
                        host = host.split(":", 1)[0]
                    self.base_url = f"{protocol}://{host}:{port}/{path}"
                else:
                    if ":" in rest:
                        host = rest.split(":", 1)[0]
                    else:
                        host = rest
                    self.base_url = f"{protocol}://{host}:{port}"
            
        self.session_endpoint = f"{self.base_url}/api/whatsapp/session"
        logger.info(f"Using session endpoint: {self.session_endpoint}")
        
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
            },
            # Test with API key in payload
            {
                "phone_number": "1234567890",
                "session_id": "test_session",
                "api_key": "test_api_key_123"
            },
            # Test with JSON format phone_number
            {
                "phone_number": {"countryCode": "1", "number": "1234567890"},
                "session_id": "test_session"
            },
            # Test with JSON format session properties
            {
                "phone_number": "1234567890",
                "session_id": "test_session",
                "session_data": {
                    "type": "whatsapp",
                    "client_id": "test_client"
                }
            },
            # Test without session_id (some APIs auto-generate it)
            {
                "phone_number": "1234567890"
            },
            # Test with device details
            {
                "phone_number": "1234567890",
                "session_id": "test_session",
                "device": {
                    "name": "Test Device",
                    "platform": "android"
                }
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
        payloads = [
            # Basic payload
            {
                "phone_number": "1234567890",
                "session_id": "test_session"
            },
            # Payload with possible version field
            {
                "phone_number": "1234567890",
                "session_id": "test_session",
                "version": "1.0"
            }
        ]
        
        results = []
        
        for payload in payloads:
            logger.info(f"Making request with detailed logging: {payload}")
            
            try:
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
                
                # Try to extract more detailed error info
                response_body = ""
                response_json = {}
                try:
                    response_json = response.json()
                    response_body = json.dumps(response_json, indent=2)
                    
                    # Log detailed validation errors if available
                    if response.status_code == 422 and "detail" in response_json:
                        logger.info(f"Validation errors: {json.dumps(response_json['detail'], indent=2)}")
                except:
                    response_body = response.text
                    
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response body: {response_body}")
                
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
                        "body": response_body,
                        "json": response_json
                    }
                }
                
                results.append(result)
                
            except requests.RequestException as e:
                logger.error(f"Request error: {str(e)}")
                results.append({
                    "error": str(e),
                    "request": {
                        "url": self.session_endpoint,
                        "method": "POST",
                        "payload": payload
                    }
                })
        
        return results
        
    def try_common_api_endpoints(self) -> Dict[str, Any]:
        """
        Try different possible endpoint variations to find the correct API endpoint.
        
        Returns:
            Results of endpoint tests
        """
        endpoints = [
            "/api/whatsapp/session",
            "/api/v1/whatsapp/session",
            "/api/v2/whatsapp/session",
            "/whatsapp/api/session",
            "/whatsapp/session",
            "/api/session/whatsapp",
            "/api/sessions",
            "/api/whatsapp-session"
        ]
        
        results = {}
        
        for endpoint in endpoints:
            test_url = f"{self.base_url.split('/api/')[0]}{endpoint}"
            logger.info(f"Testing endpoint: {test_url}")
            
            try:
                response = requests.post(
                    test_url,
                    headers=self.headers,
                    json={"phone_number": "1234567890", "session_id": "test_session"},
                    timeout=5
                )
                
                status_code = response.status_code
                try:
                    response_data = response.json()
                except:
                    response_data = {"text": response.text[:200]}
                
                results[endpoint] = {
                    "status_code": status_code,
                    "response": response_data
                }
                
                # If we got anything other than a 404, this might be the right endpoint
                if status_code != 404:
                    logger.info(f"Potential match: {endpoint} returned {status_code}")
                    
            except requests.RequestException as e:
                results[endpoint] = {"error": str(e)}
                
        return results

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
        
        # Try different API endpoints
        diagnostics["endpoint_tests"] = self.try_common_api_endpoints()
        
        # Check for connection issues
        diagnostics["connection_test"] = self._test_connection()
        
        # Analyze results and provide recommendations
        diagnostics["analysis"] = self._analyze_results(diagnostics)
        
        return diagnostics
        
    def _test_connection(self) -> Dict[str, Any]:
        """
        Test basic connectivity to the server.
        
        Returns:
            Connection test results
        """
        base_url_parts = self.base_url.split("/")
        if len(base_url_parts) >= 3:
            base_host = "/".join(base_url_parts[:3])
        else:
            base_host = self.base_url
            
        results = {}
        
        # Test basic connectivity
        try:
            logger.info(f"Testing basic connectivity to {base_host}")
            response = requests.get(base_host, timeout=5)
            results["base_connectivity"] = {
                "status_code": response.status_code,
                "success": True
            }
        except requests.RequestException as e:
            logger.error(f"Connection error to {base_host}: {str(e)}")
            results["base_connectivity"] = {
                "error": str(e),
                "success": False
            }
            
        # Check server headers
        try:
            response = requests.head(base_host, timeout=5)
            results["server_info"] = {
                "headers": dict(response.headers),
                "status_code": response.status_code
            }
            
            # Look for server information
            if "Server" in response.headers:
                results["server_type"] = response.headers["Server"]
                
        except requests.RequestException as e:
            results["server_info"] = {"error": str(e)}
            
        return results
    
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
        
        # Check if any endpoints gave better responses
        working_endpoint = None
        for endpoint, data in results.get("endpoint_tests", {}).items():
            # Check for any 2xx or specific 4xx responses that might indicate the right endpoint
            status = data.get("status_code")
            if status and (200 <= status < 300 or status in [400, 401, 403, 422]):
                working_endpoint = endpoint
                analysis["possible_issues"].append(f"The correct API endpoint might be '{endpoint}'")
                analysis["recommendations"].append(f"Try using the endpoint '{endpoint}' instead")
                break
        
        # Connection test analysis
        connection_test = results.get("connection_test", {})
        connectivity = connection_test.get("base_connectivity", {})
        if not connectivity.get("success", False):
            error_msg = connectivity.get("error", "Unknown error")
            analysis["possible_issues"].append(f"Connection issue: {error_msg}")
            analysis["recommendations"].append("Check that the server is running and accessible")
            
            # Check for common connection errors
            if "ConnectionRefusedError" in error_msg:
                analysis["recommendations"].append("The server is not accepting connections. Check if it's running on the correct port.")
            elif "ConnectTimeoutError" in error_msg:
                analysis["recommendations"].append("Connection timed out. Check network settings or firewall rules.")
        
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
                elif isinstance(response_body["detail"], dict):
                    # Some APIs return error details as a dict
                    for field, msg in response_body["detail"].items():
                        issue = f"Field '{field}': {msg}"
                        analysis["possible_issues"].append(issue)
                        analysis["recommendations"].append(
                            f"Check the format or value of field '{field}'"
                        )
        elif basic_request.get("status_code") == 404:
            analysis["possible_issues"].append("API endpoint not found (404)")
            analysis["recommendations"].append("Verify the API endpoint URL")
            
            # If we found a better endpoint, highlight it
            if working_endpoint:
                analysis["recommendations"].append(f"Use the endpoint '{working_endpoint}' instead")
        elif basic_request.get("status_code") == 401:
            analysis["possible_issues"].append("Authentication required (401)")
            analysis["recommendations"].append("Include authentication credentials in your request")
        elif basic_request.get("status_code") == 403:
            analysis["possible_issues"].append("Permission denied (403)")
            analysis["recommendations"].append("Check your authorization credentials")
        
        # Check for port mismatch
        port_mismatch = False
        url = basic_request.get("url", "")
        if url and ":" in url:
            try:
                port_part = url.split("://")[1].split("/")[0].split(":")
                if len(port_part) > 1:
                    port = int(port_part[1])
                    if port != 52589:  # Port from error message
                        port_mismatch = True
                        analysis["possible_issues"].append(f"Port mismatch: Using port {port} but error shows traffic on port 52589")
                        analysis["recommendations"].append("Try using port 52589 instead")
            except (IndexError, ValueError):
                pass
        
        # Add general recommendations if no specific ones were found
        if not analysis["recommendations"]:
            if not any_success:
                analysis["recommendations"].extend([
                    "Check the API documentation for required fields",
                    "Ensure your authentication credentials are correct",
                    "Verify the format of phone numbers (try with/without country code)",
                    "Check if the session_id needs to follow a specific format",
                    "Try using port 52589 as seen in your error message",
                    "Check if API requires a specific Content-Type or Accept header"
                ])
        
        return analysis

def main():
    """Main function to run the diagnostic script."""
    import argparse
    
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='WhatsApp API Error Diagnosis Tool')
    parser.add_argument('--url', default="http://127.0.0.1:8000", help='Base URL for the API')
    parser.add_argument('--port', type=int, help='Port to use (overrides port in URL if provided)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--headers', help='Additional headers in JSON format')
    parser.add_argument('--test-port', action='store_true', help='Test multiple common ports')
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Parse additional headers if provided
    additional_headers = {}
    if args.headers:
        try:
            additional_headers = json.loads(args.headers)
            logger.info(f"Using additional headers: {additional_headers}")
        except json.JSONDecodeError:
            logger.error(f"Could not parse headers JSON: {args.headers}")
    
    # Try multiple ports if requested
    if args.test_port:
        common_ports = [8000, 8080, 3000, 5000, 8888, 9000, 52589]
        logger.info(f"Testing multiple ports: {common_ports}")
        
        for port in common_ports:
            logger.info(f"\n--- Testing with port {port} ---")
            diagnoser = WhatsAppErrorDiagnoser(args.url, port)
            for header, value in additional_headers.items():
                diagnoser.headers[header] = value
            
            # Test basic request
            status_code, response = diagnoser.test_basic_request()
            logger.info(f"Port {port} basic request result: {status_code}")
            
            # If successful or got a 422, it might be the right port
            if status_code in [200, 201, 422]:
                logger.info(f"Port {port} returned status {status_code} - possible match!")
                # Run full diagnostics on this port
                results = diagnoser.run_diagnostics()
                logger.info(f"Results for port {port}:")
                logger.info(json.dumps(results["analysis"], indent=2))
                
                # Save port-specific results
                with open(f"whatsapp_api_diagnostics_port_{port}.json", "w") as f:
                    json.dump(results, f, indent=2)
    else:
        # Normal single-port run
        logger.info(f"Starting WhatsApp API error diagnosis with base URL: {args.url}")
        diagnoser = WhatsAppErrorDiagnoser(args.url, args.port)
        
        # Add any additional headers
        for header, value in additional_headers.items():
            diagnoser.headers[header] = value
        
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
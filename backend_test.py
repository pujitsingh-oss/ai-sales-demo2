import requests
import sys
import json
from datetime import datetime

class SalesTrainingAPITester:
    def __init__(self, base_url="https://salesgenie-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                    elif isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                    return True, response_data
                except:
                    print(f"   Response: {response.text[:100]}...")
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout (30s)")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "", 200)

    def test_get_all_scenarios(self):
        """Test getting all 60 scenarios"""
        success, response = self.run_test("Get All Scenarios", "GET", "scenarios", 200)
        if success and isinstance(response, list):
            if len(response) == 60:
                print(f"   ✅ Correct number of scenarios: {len(response)}")
                # Check first scenario structure
                if response and all(key in response[0] for key in ['id', 'category', 'objection', 'context', 'suggested_response']):
                    print(f"   ✅ Scenario structure is correct")
                else:
                    print(f"   ⚠️  Scenario structure may be incomplete")
            else:
                print(f"   ⚠️  Expected 60 scenarios, got {len(response)}")
        return success, response

    def test_get_categories(self):
        """Test getting scenario categories"""
        success, response = self.run_test("Get Scenario Categories", "GET", "scenarios/categories", 200)
        if success and isinstance(response, dict) and 'categories' in response:
            categories = response['categories']
            print(f"   ✅ Found {len(categories)} categories: {categories[:3]}...")
        return success, response

    def test_get_practice_scenarios(self):
        """Test getting 10 random practice scenarios"""
        success, response = self.run_test("Get Practice Scenarios", "GET", "scenarios/practice", 200)
        if success and isinstance(response, list):
            if len(response) == 10:
                print(f"   ✅ Correct number of practice scenarios: {len(response)}")
            else:
                print(f"   ⚠️  Expected 10 scenarios, got {len(response)}")
        return success, response

    def test_handle_objection(self):
        """Test objection handling with AI"""
        test_data = {
            "objection_text": "Your commission is too high.",
            "language": "English",
            "scenario_id": 1
        }
        success, response = self.run_test("Handle Objection", "POST", "objection/handle", 200, test_data)
        if success and isinstance(response, dict):
            if 'response' in response:
                print(f"   ✅ AI response generated (length: {len(response['response'])} chars)")
                if 'scenario_used' in response and response['scenario_used']:
                    print(f"   ✅ Scenario context used")
            else:
                print(f"   ⚠️  Response missing 'response' field")
        return success, response

    def test_handle_objection_without_scenario(self):
        """Test objection handling without specific scenario"""
        test_data = {
            "objection_text": "I don't have time for this right now.",
            "language": "English"
        }
        success, response = self.run_test("Handle Objection (No Scenario)", "POST", "objection/handle", 200, test_data)
        if success and isinstance(response, dict):
            if 'response' in response:
                print(f"   ✅ AI response generated without scenario (length: {len(response['response'])} chars)")
        return success, response

    def test_practice_feedback(self):
        """Test practice feedback generation"""
        test_data = {
            "scenario_id": 1,
            "user_response": "I understand your concern about the commission. Let me show you the value we provide that justifies this investment.",
            "response_type": "text"
        }
        success, response = self.run_test("Practice Feedback", "POST", "practice/feedback", 200, test_data)
        if success and isinstance(response, dict):
            if 'feedback' in response:
                print(f"   ✅ Feedback generated (length: {len(response['feedback'])} chars)")
                if 'score' in response and response['score']:
                    print(f"   ✅ Score provided: {response['score']}/10")
                if 'suggestions' in response and response['suggestions']:
                    print(f"   ✅ {len(response['suggestions'])} suggestions provided")
        return success, response

    def test_multilingual_support(self):
        """Test multilingual objection handling"""
        test_data = {
            "objection_text": "Bahut mehenga hai, itna budget nahi hai mera.",
            "language": "Hindi"
        }
        success, response = self.run_test("Multilingual Support", "POST", "objection/handle", 200, test_data)
        if success and isinstance(response, dict) and 'response' in response:
            print(f"   ✅ Hindi objection processed successfully")
        return success, response

    def test_error_handling(self):
        """Test error handling with invalid data"""
        # Test empty objection
        test_data = {
            "objection_text": "",
            "language": "English"
        }
        success, response = self.run_test("Error Handling (Empty Objection)", "POST", "objection/handle", 200, test_data)
        
        # Test invalid scenario ID for practice
        test_data = {
            "scenario_id": 999,
            "user_response": "Test response",
            "response_type": "text"
        }
        success2, response2 = self.run_test("Error Handling (Invalid Scenario)", "POST", "practice/feedback", 404, test_data)
        
        return success2, response2

def main():
    print("🚀 Starting Sales Training Assistant API Tests")
    print("=" * 60)
    
    tester = SalesTrainingAPITester()
    
    # Run all tests
    print("\n📋 Testing Basic Endpoints...")
    tester.test_root_endpoint()
    
    print("\n📋 Testing Scenario Endpoints...")
    tester.test_get_all_scenarios()
    tester.test_get_categories()
    tester.test_get_practice_scenarios()
    
    print("\n🤖 Testing AI Integration...")
    tester.test_handle_objection()
    tester.test_handle_objection_without_scenario()
    tester.test_practice_feedback()
    
    print("\n🌍 Testing Multilingual Support...")
    tester.test_multilingual_support()
    
    print("\n⚠️  Testing Error Handling...")
    tester.test_error_handling()
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! Backend is working correctly.")
        return 0
    else:
        failed = tester.tests_run - tester.tests_passed
        print(f"❌ {failed} test(s) failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
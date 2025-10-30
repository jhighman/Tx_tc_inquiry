#!/usr/bin/env python3
"""
Test script to verify the enhanced features including sponsor ID and webhook functionality.
"""

import os
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from arrestx.config import load_config
from arrestx.api import search_name, send_webhook_callback, SearchResult, Alert

def test_sponsor_id_functionality():
    """Test that sponsor ID is properly handled and included in responses."""
    print("Testing sponsor ID functionality...")
    
    config = load_config("config.yaml")
    
    try:
        # Test with sponsor ID
        result = search_name(
            name="Smith", 
            cfg=config, 
            force_update=False,
            person_bio="test-person-123",
            organization="test-org",
            sponsor_id="sponsor-456",
            webhook_url=None
        )
        
        # Check standard format
        result_dict = result.to_dict()
        print(f"Standard format includes sponsor_id: {'sponsor_id' in result_dict}")
        if 'sponsor_id' in result_dict:
            print(f"Sponsor ID value: {result_dict['sponsor_id']}")
        
        # Check enterprise format
        enterprise_result = result.to_enterprise_format()
        summary = enterprise_result.get('summary', {})
        print(f"Enterprise format includes sponsorId: {'sponsorId' in summary}")
        if 'sponsorId' in summary:
            print(f"Enterprise sponsorId value: {summary['sponsorId']}")
        
        # Verify removed attributes are not present
        removed_attrs = ['selectedDTOAttributes', 'organization', 'hashString', 'eventWorkFlow', 'archived', 'packageId', 'auditId']
        events = enterprise_result.get('events', [])
        if events:
            event = events[0]
            missing_attrs = [attr for attr in removed_attrs if attr not in event]
            print(f"Removed attributes successfully excluded: {len(missing_attrs) == len(removed_attrs)}")
            if len(missing_attrs) != len(removed_attrs):
                present_attrs = [attr for attr in removed_attrs if attr in event]
                print(f"Still present: {present_attrs}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_webhook_functionality():
    """Test webhook callback functionality."""
    print("\nTesting webhook functionality...")
    
    # Mock the requests.post call
    with patch('requests.post') as mock_post:
        # Configure mock to return successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Create a test result with alerts
        alerts = [Alert(
            name="SMITH, JOHN DOE",
            booking_no="2025001234",
            description="THEFT",
            identifier="12345",
            book_in_date="2025-10-30",
            source_file="01.PDF"
        )]
        
        result = SearchResult(
            name="John Smith",
            alerts=alerts,
            records_checked=100,
            last_update=None,
            person_bio="test-person-123",
            organization="test-org",
            sponsor_id="sponsor-456",
            webhook_url="https://example.com/webhook"
        )
        
        # Test webhook sending
        success = send_webhook_callback(result, "https://example.com/webhook")
        
        print(f"Webhook sent successfully: {success}")
        print(f"Requests.post called: {mock_post.called}")
        
        if mock_post.called:
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            print(f"Webhook payload includes sponsorId: {'sponsorId' in payload}")
            print(f"Webhook payload includes personBioId: {'personBioId' in payload}")
            print(f"Webhook payload includes alerts: {'alerts' in payload}")
            
        return success
        
def test_enterprise_format_cleanup():
    """Test that specified attributes are removed from enterprise format."""
    print("\nTesting enterprise format attribute removal...")
    
    config = load_config("config.yaml")
    
    try:
        result = search_name(
            name="Smith", 
            cfg=config, 
            force_update=False,
            sponsor_id="sponsor-789"
        )
        
        enterprise_result = result.to_enterprise_format()
        
        # Check that removed attributes are not present
        removed_attrs = ['selectedDTOAttributes', 'organization', 'hashString', 'eventWorkFlow', 'archived', 'packageId', 'auditId']
        
        events = enterprise_result.get('events', [])
        all_clean = True
        
        for event in events:
            for attr in removed_attrs:
                if attr in event:
                    print(f"❌ Found removed attribute '{attr}' in event")
                    all_clean = False
        
        if all_clean:
            print("✅ All specified attributes successfully removed from enterprise format")
        
        # Check that summary includes sponsorId but not organization
        summary = enterprise_result.get('summary', {})
        has_sponsor = 'sponsorId' in summary
        has_org = 'organization' in summary
        
        print(f"Summary includes sponsorId: {has_sponsor}")
        print(f"Summary excludes organization: {not has_org}")
        
        return all_clean and has_sponsor and not has_org
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def main():
    """Run all enhanced feature tests."""
    print("🧪 Testing enhanced features...")
    print("=" * 50)
    
    # Test 1: Sponsor ID functionality
    test1_passed = test_sponsor_id_functionality()
    
    # Test 2: Webhook functionality
    test2_passed = test_webhook_functionality()
    
    # Test 3: Enterprise format cleanup
    test3_passed = test_enterprise_format_cleanup()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"Test 1 (Sponsor ID): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (Webhook): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"Test 3 (Enterprise cleanup): {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed and test3_passed:
        print("\n🎉 All enhanced feature tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
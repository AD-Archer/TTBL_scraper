#!/usr/bin/env python3
"""
Fabrik API Test Script

Tests all known Fabrik API listids to determine access patterns.
Saves comprehensive report of findings.

Author: Agent 4
Date: January 9, 2026
Version: 1.1
"""

import requests
import sys
import json
from pathlib import Path

BASE_URL = "https://results.ittf.link/index.php"

# List IDs from Agent 3's discovery
LIST_IDS_TO_TEST = {
    "31": "Player matches (primary - Agent 3's finding)",
    "55": "WTT results (Agent 3)",
    "70": "Tournament results (Agent 3)",
    "102": "Player ranking history (Agent 3)"
}

def test_endpoint(listid: int, params: dict = None, year: int = 2025) -> dict:
    """Test a specific Fabrik API endpoint."""
    url = f"{BASE_URL}?option=com_fabrik&view=list&listid={listid}&format=json"
    if params:
        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        url += f"&{param_str}"
    
    print(f"\nTesting listid={listid} with params: {params or 'default'}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'ITTF-Scraper/1.1 (Fabrik API Test)'
        })
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        content_type = response.headers.get('Content-Type', '')
        is_json = 'application/json' in content_type or 'json' in content_type.lower()
        
        content_type = response.headers.get('Content-Type', '')
        is_json = 'application/json' in content_type or 'json' in content_type.lower()

        if is_json:
            data = response.json()
            item_count = len(data) if isinstance(data, list) else 1
            print(f"Response is JSON with {item_count} items")
            if isinstance(data, list) and item_count > 0:
                print(f"Sample item: {json.dumps(data[0], indent=2)}")
            return {
                'success': True,
                'listid': listid,
                'content_type': 'json',
                'item_count': item_count,
                'sample': data[0] if isinstance(data, list) else data
            }
            else:
                # Single object
                print(f"Sample: {json.dumps(data, indent=2)[:500]}")
                return {
                    'success': True,
                    'listid': listid,
                    'content_type': 'json',
                    'item_count': 1,
                    'sample': data
                }
            else:
                # Single object
                print(f"Sample: {json.dumps(data, indent=2)[:500]}")
                return {
                    'success': True,
                    'listid': listid,
                    'content_type': 'json',
                    'item_count': 1,
                    'sample': data,
                    'data': data
                }
        else:
            # HTML response
            html = response.text
            print(f"Response is HTML (first 500 chars):")
            print(html[:500])
            
            # Check for common Fabrik responses
            if 'Sorry' in html or 'not published' in html:
                return {
                    'success': False,
                    'listid': listid,
                    'content_type': 'html',
                    'error': 'Access denied - list not published'
                }
            elif 'login' in html or 'sign in' in html:
                return {
                    'success': False,
                    'listid': listid,
                    'content_type': 'html',
                    'error': 'Authentication required'
                }
            else:
                return {
                    'success': False,
                    'listid': listid,
                    'content_type': 'html',
                    'error': 'Unknown HTML response',
                    'html_sample': html[:200]
                }
                
    except Exception as e:
        print(f"Error: {e}")
        return {
            'success': False,
            'listid': listid,
            'error': str(e)
        }

def test_all_endpoints():
    """Test all known Fabrik listids."""
    print("=" * 70)
    print("Fabrik API Endpoint Test")
    print("Agent 4 - Access Verification")
    print("=" * 70)
    print()
    
    results = {}
    
    for listid, description in LIST_IDS_TO_TEST.items():
        print(f"\nTesting {description}")
        print("-" * 70)
        
        # Test without year filter
        result_default = test_endpoint(listid, params=None, year=None)
        results[f"listid_{listid}_default"] = result_default
        
        # Test with 2025 year filter
        result_2025 = test_endpoint(listid, params={"vw_matches___yr[value]": "2025"}, year=2025)
        results[f"listid_{listid}_year_2025"] = result_2025
    
    return results

def generate_report(results: dict) -> dict:
    """Generate summary report."""
    report = {
        'test_time': None,
        'tested_listids': list(results.keys()),
        'summary': {
            'working_endpoints': [],
            'access_denied': [],
            'auth_required': [],
            'unknown_errors': []
        },
        'detailed_results': results
    }
    
    # Analyze results
    for listid, result in results.items():
        if not result.get('success', False):
            if 'Access denied' in result.get('error', ''):
                report['summary']['access_denied'].append(listid)
            elif 'Authentication' in result.get('error', ''):
                report['summary']['auth_required'].append(listid)
            else:
                report['summary']['unknown_errors'].append(f"{listid}: {result.get('error')}")
        else:
            report['summary']['working_endpoints'].append(listid)
    
    return report

def save_report(report: dict, filename: str = "fabrik_api_test_report.json"):
    """Save report to file."""
    output_dir = Path("./data/wtt_ittf")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / filename
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved to: {output_file}")

def main():
    print("=" * 70)
    print("Fabrik API Endpoint Test Tool")
    print("Agent 4 - Access Verification")
    print("=" * 70)
    print()
    print("Testing all known Fabrik API listids")
    print("This will help determine which endpoints are accessible")
    print()
    
    results = test_all_endpoints()
    report = generate_report(results)
    save_report(report)
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print()
    print(f"Total endpoints tested: {len(results)}")
    print(f"Working endpoints: {len(report['summary']['working_endpoints'])}")
    print(f"Access denied: {len(report['summary']['access_denied'])}")
    print(f"Auth required: {len(report['summary']['auth_required'])}")
    print(f"Unknown errors: {len(report['summary']['unknown_errors'])}")
    print("=" * 70)

if __name__ == "__main__":
    main()

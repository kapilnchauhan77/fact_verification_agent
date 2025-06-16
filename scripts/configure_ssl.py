#!/usr/bin/env python3
"""
SSL Configuration script for the Fact Check Agent
Provides options to configure SSL behavior and suppress warnings
"""

import urllib3
import ssl
import logging

def configure_ssl_settings(suppress_warnings=True, strict_ssl=True):
    """
    Configure SSL settings for the fact-checking agent
    
    Args:
        suppress_warnings: Whether to suppress SSL warnings
        strict_ssl: Whether to enforce strict SSL verification
    """
    
    print("🔒 CONFIGURING SSL SETTINGS")
    print("=" * 40)
    
    if suppress_warnings:
        # Disable urllib3 SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        print("✅ SSL warnings suppressed")
    
    if strict_ssl:
        # Enable strict SSL verification
        ssl._create_default_https_context = ssl.create_default_context
        print("✅ Strict SSL verification enabled")
    else:
        # Allow unverified SSL (not recommended for production)
        ssl._create_default_https_context = ssl._create_unverified_context
        print("⚠️  SSL verification relaxed (not recommended for production)")
    
    print()
    print("🛡️  SSL Configuration Complete")
    print()
    print("📋 Current Settings:")
    print(f"   • SSL Warnings Suppressed: {suppress_warnings}")
    print(f"   • Strict SSL Verification: {strict_ssl}")
    print()
    
    if not strict_ssl:
        print("⚠️  WARNING: Running with relaxed SSL verification")
        print("   This is not recommended for production use")
        print("   Only use this for testing or development")

def main():
    """Configure SSL settings based on environment"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Configure SSL settings for Fact Check Agent")
    parser.add_argument('--suppress-warnings', action='store_true', 
                       help='Suppress SSL warnings')
    parser.add_argument('--strict-ssl', action='store_true', default=True,
                       help='Enable strict SSL verification (default: True)')
    parser.add_argument('--relax-ssl', action='store_true',
                       help='Disable strict SSL verification (not recommended)')
    
    args = parser.parse_args()
    
    # Override strict_ssl if relax_ssl is specified
    if args.relax_ssl:
        strict_ssl = False
    else:
        strict_ssl = args.strict_ssl
    
    configure_ssl_settings(
        suppress_warnings=args.suppress_warnings,
        strict_ssl=strict_ssl
    )

if __name__ == "__main__":
    main()
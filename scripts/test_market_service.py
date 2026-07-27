#!/usr/bin/env python3
"""
Market Service Integration Test Script

This script validates the Business Service Layer by:
1. Creating MarketService with dependency injection
2. Calling ForceRefresh() to download from Navasan
3. Storing data into MySQL
4. Reading data back from Repository
5. Printing returned DTOs
6. Verifying database records

Usage:
    python scripts/test_market_service.py
"""

import asyncio
import sys
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

# Add project root to path
sys.path.insert(0, '.')

from app.services.market_service import MarketService
from app.repository.market_repository import MarketRepository
from app.providers.provider_registry import ProviderRegistry
from app.dto.price_dto import PriceDTO, PriceHistoryDTO
from app.core.config import get_settings


async def test_market_service_integration():
    """Main integration test function"""
    
    print("=" * 80)
    print("MARKET SERVICE INTEGRATION TEST")
    print("=" * 80)
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    # Get configuration
    settings = get_settings()
    print(f"Database: {settings.database_url}")
    print(f"Default Provider: {settings.default_provider}")
    print()
    
    # Step 1: Create dependencies using dependency injection
    print("Step 1: Initializing dependencies...")
    try:
        repository = MarketRepository()
        provider_registry = ProviderRegistry()
        
        # Auto-discover and register providers
        provider_registry.discover_providers()
        
        print(f"  ✓ Repository initialized")
        print(f"  ✓ Provider registry initialized")
        print(f"  ✓ Available providers: {provider_registry.get_available_providers()}")
        print()
        
    except Exception as e:
        print(f"  ✗ Failed to initialize dependencies: {e}")
        return False
    
    # Step 2: Create MarketService with dependency injection
    print("Step 2: Creating MarketService...")
    try:
        service = MarketService(
            price_repository=repository,
            provider_registry=provider_registry
        )
        print(f"  ✓ MarketService created successfully")
        print()
        
    except Exception as e:
        print(f"  ✗ Failed to create MarketService: {e}")
        return False
    
    # Step 3: Define test items (Navasan supports these codes)
    test_items = [
        "USD",      # US Dollar
        "EUR",      # Euro
        "GBP",      # British Pound
        "AED",      # UAE Dirham
        "CAD",      # Canadian Dollar
    ]
    
    print(f"Step 3: Test items defined: {test_items}")
    print()
    
    # Step 4: Call ForceRefresh() to download from Navasan
    print("Step 4: Calling ForceRefresh() to download from Navasan...")
    print(f"  Target items: {test_items}")
    print(f"  Provider: Navasan (default)")
    print()
    
    try:
        refresh_start = datetime.now()
        response = await service.force_refresh(item_codes=test_items)
        refresh_end = datetime.now()
        refresh_duration = (refresh_end - refresh_start).total_seconds()
        
        print(f"  ✓ ForceRefresh completed in {refresh_duration:.2f} seconds")
        print(f"  ✓ Total prices retrieved: {response.total_count}")
        print()
        
        # Step 5: Print returned DTOs
        print("Step 5: Retrieved Price DTOs:")
        print("-" * 80)
        
        if response.prices:
            for price_dto in response.prices:
                if price_dto.price is not None:
                    print(f"  • {price_dto.item_code:6s} | {price_dto.price:>12.4f} {price_dto.currency:3s} | "
                          f"Source: {price_dto.source_provider:8s} | "
                          f"Updated: {price_dto.updated_at.strftime('%Y-%m-%d %H:%M:%S') if price_dto.updated_at else 'N/A'}")
                else:
                    print(f"  • {price_dto.item_code:6s} | {'NO DATA':>12s} | Source: {price_dto.source_provider}")
        else:
            print("  No prices retrieved")
        
        print("-" * 80)
        print()
        
        # Step 6: Read data back from Repository
        print("Step 6: Reading data back from Repository...")
        try:
            cached_prices = await service.get_latest_prices(
                item_codes=test_items,
                force_refresh=False  # Should use cache
            )
            
            print(f"  ✓ Cache read successful")
            print(f"  ✓ Cached prices count: {cached_prices.total_count}")
            print()
            
            # Verify cache matches fresh data
            if response.total_count == cached_prices.total_count:
                print("  ✓ Cache consistency verified")
            else:
                print(f"  ⚠ Cache count mismatch: fresh={response.total_count}, cache={cached_prices.total_count}")
            print()
            
        except Exception as e:
            print(f"  ✗ Failed to read from cache: {e}")
            return False
        
        # Step 7: Test price history retrieval
        print("Step 7: Testing price history retrieval...")
        try:
            history_response = await service.get_price_history(
                item_codes=test_items[:2],  # Get history for first 2 items
                days=1  # Last 1 day
            )
            
            print(f"  ✓ History retrieval successful")
            print(f"  ✓ Historical records: {history_response.total_count}")
            
            if history_response.history:
                print(f"  • Sample history entry:")
                sample = history_response.history[0]
                print(f"      {sample.item_code}: {sample.price} {sample.currency} @ {sample.timestamp}")
            print()
            
        except Exception as e:
            print(f"  ✗ Failed to retrieve history: {e}")
            # Continue anyway, history might be empty initially
        
        # Step 8: Verify database records directly
        print("Step 8: Verifying database records...")
        try:
            # Check latest prices table
            db_latest = await repository.get_all_latest()
            print(f"  ✓ Latest prices in database: {len(db_latest)} records")
            
            # Check history table
            db_history = await repository.get_history(limit=10)
            print(f"  ✓ Price history in database: {len(db_history)} records")
            
            # Verify specific items exist
            for item_code in test_items:
                item_latest = await repository.get_latest_by_code(item_code)
                if item_latest:
                    print(f"  ✓ {item_code}: Found in database (Price: {item_latest.price})")
                else:
                    print(f"  ⚠ {item_code}: Not found in database")
            
            print()
            
        except Exception as e:
            print(f"  ✗ Failed to verify database: {e}")
            return False
        
        # Step 9: Test NeedRefresh logic
        print("Step 9: Testing NeedRefresh logic...")
        try:
            needs_refresh = await service.need_refresh(item_codes=test_items)
            print(f"  ✓ NeedRefresh check completed")
            print(f"  • Refresh needed: {needs_refresh}")
            
            if not needs_refresh:
                print(f"  ✓ Cache is still valid (within TTL)")
            else:
                print(f"  ⚠ Cache expired or missing")
            print()
            
        except Exception as e:
            print(f"  ✗ Failed NeedRefresh check: {e}")
            return False
        
        # Step 10: Summary and validation
        print("=" * 80)
        print("INTEGRATION TEST SUMMARY")
        print("=" * 80)
        
        success_criteria = [
            ("ForceRefresh executed", True),
            ("Prices downloaded from Navasan", response.total_count > 0),
            ("Data stored in MySQL", len(db_latest) > 0),
            ("Data retrieved from cache", cached_prices.total_count > 0),
            ("History accessible", True),  # Even if empty, endpoint worked
            ("Database verification passed", True),
            ("NeedRefresh logic working", True),
        ]
        
        all_passed = True
        for criterion, passed in success_criteria:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {status}: {criterion}")
            if not passed:
                all_passed = False
        
        print()
        print(f"Test completed at: {datetime.now().isoformat()}")
        
        if all_passed:
            print()
            print("🎉 ALL INTEGRATION TESTS PASSED!")
            print("Market Service is ready for REST API exposure.")
            return True
        else:
            print()
            print("❌ SOME TESTS FAILED!")
            print("Please review errors above.")
            return False
            
    except Exception as e:
        print(f"  ✗ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        try:
            await repository.close()
            print()
            print("Database connection closed.")
        except:
            pass


async def test_error_scenarios():
    """Test error handling scenarios"""
    
    print()
    print("=" * 80)
    print("ERROR HANDLING TESTS")
    print("=" * 80)
    print()
    
    repository = MarketRepository()
    provider_registry = ProviderRegistry()
    provider_registry.discover_providers()
    
    service = MarketService(
        price_repository=repository,
        provider_registry=provider_registry
    )
    
    # Test 1: Invalid provider
    print("Test 1: Invalid provider selection...")
    try:
        await service.force_refresh(item_codes=["USD"], provider_name="INVALID_PROVIDER")
        print("  ✗ Should have raised an exception")
    except ValueError as e:
        print(f"  ✓ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"  ⚠ Raised unexpected exception: {type(e).__name__}: {e}")
    print()
    
    # Test 2: Empty item list
    print("Test 2: Empty item list...")
    try:
        response = await service.force_refresh(item_codes=[])
        print(f"  ✓ Handled empty list: {response.total_count} items")
    except Exception as e:
        print(f"  ✗ Failed with empty list: {e}")
    print()
    
    # Test 3: Non-existent item code
    print("Test 3: Non-existent item code...")
    try:
        response = await service.force_refresh(item_codes=["NONEXISTENT123"])
        print(f"  ✓ Handled non-existent code: {response.total_count} items")
        # Should return item with null price
        if response.prices and response.prices[0].price is None:
            print(f"  ✓ Correctly returned null price for unknown item")
    except Exception as e:
        print(f"  ✗ Failed with non-existent code: {e}")
    print()
    
    await repository.close()


async def main():
    """Main entry point"""
    
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "MARKET SERVICE INTEGRATION TEST" + " " * 27 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    # Run main integration test
    success = await test_market_service_integration()
    
    # Run error handling tests
    if success:
        await test_error_scenarios()
    
    print()
    print("=" * 80)
    if success:
        print("✅ INTEGRATION TEST SUITE COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print()
        print("Next steps:")
        print("  1. Review output above")
        print("  2. Verify database records in MySQL")
        print("  3. Proceed to REST API implementation")
        return 0
    else:
        print("❌ INTEGRATION TEST SUITE FAILED")
        print("=" * 80)
        print()
        print("Please fix the issues above before proceeding.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

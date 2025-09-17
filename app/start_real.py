#!/usr/bin/env python3
"""
Start Real Trading Dashboard with MongoDB
Script khởi động ứng dụng trading thật với MongoDB persistence
"""

import uvicorn
import sys
import os
import subprocess
import time
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))


def check_mongodb():
    """Check if MongoDB is running"""
    try:
        import pymongo
        client = pymongo.MongoClient(
            'mongodb://localhost:27017',
            serverSelectionTimeoutMS=2000)
        client.admin.command('ismaster')
        client.close()
        print("✅ MongoDB is running")
        return True
    except Exception:
        print("⚠️ MongoDB is not running")
        return False


def start_mongodb():
    """Try to start MongoDB service"""
    try:
        # Try different MongoDB start commands
        commands = [
            ['sudo', 'systemctl', 'start', 'mongod'],
            ['brew', 'services', 'start', 'mongodb-community'],
            ['mongod', '--dbpath', '/data/db'],
        ]

        for cmd in commands:
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                print(f"✅ Started MongoDB with: {' '.join(cmd)}")
                time.sleep(2)  # Wait for MongoDB to start
                if check_mongodb():
                    return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue

        print("❌ Could not start MongoDB automatically")
        print("💡 Please start MongoDB manually:")
        print("   - Ubuntu/Debian: sudo systemctl start mongod")
        print("   - macOS: brew services start mongodb-community")
        print("   - Manual: mongod --dbpath /data/db")
        return False

    except Exception as e:
        print(f"❌ Error starting MongoDB: {e}")
        return False


def main():
    print("🚀 Starting Real Trading Dashboard...")
    print("📊 Real data only - No mock data")
    print("🔄 With MongoDB persistence")
    print("📡 With WebSocket real-time updates")
    print()

    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return 1

    # Check if MongoDB is available
    mongodb_available = check_mongodb()
    if not mongodb_available:
        print("🔄 Trying to start MongoDB...")
        mongodb_available = start_mongodb()

    if not mongodb_available:
        print("\n⚠️ MongoDB not available - continuing without persistence")
        print("💡 Some features may be limited")

    # Check FiinQuantX credentials
    fiin_user = os.getenv('TRADING_FIIN_USERNAME', 'DSTC_19@fiinquant.vn')
    fiin_pass = os.getenv('TRADING_FIIN_PASSWORD', 'Fiinquant0606')

    print(f"\n🔑 FiinQuantX User: {fiin_user}")
    print("🔑 FiinQuantX Password: [HIDDEN]")

    # Display access information
    print(f"\n📊 Dashboard: http://localhost:8000")
    print(f"📈 API docs: http://localhost:8000/docs")
    print(f"📡 WebSocket: ws://localhost:8000/ws")
    print(f"\n🛑 Press Ctrl+C to stop")
    print("=" * 50)

    try:
        # Start the application
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Shutting down gracefully...")
        return 0
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

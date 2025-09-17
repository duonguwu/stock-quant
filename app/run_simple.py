#!/usr/bin/env python3
"""
Simple script to run the trading signals app with monitoring
"""

import uvicorn
import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from config.settings import get_settings


def check_dependencies():
    """Check if required services are running"""
    import socket
    
    def check_port(host, port, service_name):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                print(f"✅ {service_name} is running on {host}:{port}")
                return True
            else:
                print(f"❌ {service_name} is NOT running on {host}:{port}")
                return False
        except Exception as e:
            print(f"❌ Error checking {service_name}: {e}")
            return False
    
    print("🔍 Checking required services...")
    
    # Check MongoDB
    mongodb_ok = check_port("localhost", 27017, "MongoDB")
    
    # Check Redis
    redis_ok = check_port("localhost", 6379, "Redis")
    
    if not mongodb_ok:
        print("\n🚨 MongoDB is required!")
        print("Start with: docker run -d --name mongo-container -p 27017:27017 mongo:latest")
        
    if not redis_ok:
        print("\n🚨 Redis is required!")
        print("Start with: docker run -d --name redis-container -p 6379:6379 redis:7-alpine")
    
    return mongodb_ok and redis_ok


def show_app_info():
    """Show application information"""
    settings = get_settings()
    
    print("\n" + "="*60)
    print("🚀 TRADING SIGNALS APP")
    print("="*60)
    print(f"📊 Dashboard: http://localhost:8000")
    print(f"🔌 WebSocket: ws://localhost:8000/ws/signals")
    print(f"📱 API Docs: http://localhost:8000/docs")
    print("="*60)
    print(f"🎯 Tickers: {settings.default_tickers}")
    print(f"🔑 FiinQuantX: {settings.fiin_username}")
    print(f"💾 MongoDB: {settings.mongodb_url}")
    print("="*60)
    print("\n🎯 HOẠT ĐỘNG CỦA ỨNG DỤNG:")
    print("1. Fetch dữ liệu 15m từ FiinQuantX")
    print("2. Feature engineering (7 → 56 columns)")
    print("3. Generate signals với multiple strategies")
    print("4. Lưu vào MongoDB và broadcast qua WebSocket")
    print("5. Gửi Telegram alerts cho premium signals")
    print("6. Cập nhật mỗi 5 phút")
    print("\n🎉 App sẽ tự động generate signals và hiển thị trên dashboard!")
    print("👆 Mở http://localhost:8000 để xem real-time dashboard")


async def monitor_app():
    """Monitor app status"""
    print("\n🔄 App is running... Press Ctrl+C to stop")
    print("📊 Monitoring signals generation every 5 minutes...")
    
    try:
        while True:
            await asyncio.sleep(60)  # Check every minute
            print(f"⏱️  App running... {asyncio.get_event_loop().time():.0f}s")
    except KeyboardInterrupt:
        print("\n🛑 Stopping app...")


def main():
    """Main function"""
    print("🚀 Starting Trading Signals Dashboard...")
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please start required services and try again")
        return 1
    
    # Show app info
    show_app_info()
    
    try:
        # Run FastAPI app
        print("\n🌟 Starting web server...")
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,  # Disable reload for production
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n🛑 App stopped by user")
        return 0
    except Exception as e:
        print(f"\n❌ App crashed: {e}")
        return 1


if __name__ == "__main__":
    exit(main()) 
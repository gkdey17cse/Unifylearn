# src/app/utils/logger.py
import os


class Logger:
    def __init__(self, debug_mode=False):
        self.debug_mode = (
            debug_mode or os.getenv("DEBUG_MODE", "false").lower() == "true"
        )

    def info(self, message):
        """Important information that should always be shown"""
        print(f"ℹ️  {message}")

    def success(self, message):
        """Success messages"""
        print(f"✅ {message}")

    def warning(self, message):
        """Warning messages"""
        print(f"⚠️  {message}")

    def error(self, message):
        """Error messages"""
        print(f"❌ {message}")

    def debug(self, message):
        """Debug messages - only shown in debug mode"""
        if self.debug_mode:
            print(f"🐛 {message}")

    def query(self, message):
        """Query-related messages"""
        print(f"🔍 {message}")

    def database(self, message):
        """Database operation messages"""
        print(f"🗄️  {message}")

    def llm(self, message):
        """LLM-related messages"""
        print(f"🤖 {message}")

    def aggregation(self, message):
        """Aggregation-specific messages"""
        print(f"📊 {message}")


# Global logger instance
logger = Logger()
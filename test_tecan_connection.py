"""Simple test script to verify Tecan Fluent SiLA2 connection."""

from tecan import Fluent

def main():
    print("Attempting to connect to Tecan Fluent...")

    # Create Fluent instance with insecure connection (for testing)
    fluent = Fluent("127.0.0.1", 50052, insecure=True)

    print("Starting Fluent...")
    fluent.start_fluent()

    print("Connection successful!")
    print("Stopping Fluent...")
    fluent.stop_fluent()

    print("Test complete!")

if __name__ == "__main__":
    main()
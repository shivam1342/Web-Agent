"""
Entry point for the Semi-Autonomous Web Interaction Agent.
"""

from agent.orchestrator import Orchestrator


def main():
    """Run the agent"""
    print("="*60)
    print("Semi-Autonomous Web Interaction Agent")
    print("Target: https://docs.python.org")
    print("Focus: Documentation exploration")
    print("="*60)
    
    # Create and run orchestrator
    orchestrator = Orchestrator(
        start_url="https://docs.python.org",
        headless=False  # Set to True for headless mode
    )
    
    try:
        orchestrator.run()
        print("\n✅ Agent exploration complete!")
        print("📄 Check logs/run_log.json for detailed execution trace")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Agent stopped by user")
    except Exception as e:
        print(f"\n\n❌ Agent encountered an error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Example script demonstrating chaos experiments usage
"""
import time
import sys
import os

# Add the parent directory to sys.path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment for framework
os.environ['CURRENT_FRAMEWORK'] = 'flask'

from genericsuite.models.chaos.chaos_experiments import (
    ChaosExperimentManager,
    chaos_test_endpoint,
    Request
)

def demo_latency_injection():
    """Demonstrate latency injection experiment"""
    print("=== Latency Injection Experiment Demo ===")
    
    manager = ChaosExperimentManager()
    
    # Start latency injection experiment
    print("Starting latency injection experiment (2s delay for 10s)...")
    result = manager.start_experiment(
        "latency_injection",
        delay_seconds=2.0,
        duration_seconds=10.0
    )
    print(f"Start result: {result}")
    
    # Replace global manager to test effects
    import genericsuite.models.chaos.chaos_experiments as chaos_module
    original_manager = chaos_module.chaos_manager
    chaos_module.chaos_manager = manager
    
    try:
        # Test the effect
        print("\nTesting latency effect...")
        mock_request = Request()
        
        start_time = time.time()
        response = chaos_test_endpoint(mock_request)
        duration = time.time() - start_time
        
        print(f"Request took {duration:.2f} seconds (should be ~2s due to latency injection)")
        print(f"Response: {response}")
        
    finally:
        # Restore global manager
        chaos_module.chaos_manager = original_manager
    
    # Stop the experiment
    print("\nStopping experiment...")
    stop_result = manager.stop_experiment("latency_injection")
    print(f"Stop result: {stop_result}")


def demo_error_injection():
    """Demonstrate error injection experiment"""
    print("\n=== Error Injection Experiment Demo ===")
    
    manager = ChaosExperimentManager()
    
    # Start error injection experiment with 50% error rate
    print("Starting error injection experiment (50% error rate for 10s)...")
    result = manager.start_experiment(
        "error_injection",
        error_rate=0.5,
        duration_seconds=10.0
    )
    print(f"Start result: {result}")
    
    # Replace global manager to test effects
    import genericsuite.models.chaos.chaos_experiments as chaos_module
    original_manager = chaos_module.chaos_manager
    chaos_module.chaos_manager = manager
    
    try:
        # Test the effect multiple times
        print("\nTesting error injection (making 10 requests)...")
        mock_request = Request()
        
        error_count = 0
        total_requests = 10
        
        for i in range(total_requests):
            try:
                response = chaos_test_endpoint(mock_request)
                if isinstance(response, dict) and response.get('error'):
                    error_count += 1
                    print(f"Request {i+1}: ERROR - {response.get('error_message', 'Unknown error')}")
                else:
                    print(f"Request {i+1}: SUCCESS")
            except Exception as e:
                error_count += 1
                print(f"Request {i+1}: EXCEPTION - {e}")
            
            time.sleep(0.1)  # Small delay between requests
        
        print(f"\nError rate: {error_count}/{total_requests} = {error_count/total_requests*100:.1f}% (expected ~50%)")
        
    finally:
        # Restore global manager
        chaos_module.chaos_manager = original_manager
    
    # Stop the experiment
    print("\nStopping experiment...")
    stop_result = manager.stop_experiment("error_injection")
    print(f"Stop result: {stop_result}")


def demo_resource_exhaustion():
    """Demonstrate resource exhaustion experiment"""
    print("\n=== Resource Exhaustion Experiment Demo ===")
    
    manager = ChaosExperimentManager()
    
    # Start resource exhaustion experiment
    print("Starting resource exhaustion experiment (consuming 50MB for 5s)...")
    result = manager.start_experiment(
        "resource_exhaustion",
        memory_mb=50,
        duration_seconds=5.0
    )
    print(f"Start result: {result}")
    
    # Monitor for a bit
    print("\nMonitoring experiment...")
    for i in range(3):
        time.sleep(1)
        status = manager.get_experiment_status("resource_exhaustion")
        print(f"Status check {i+1}: {status.get('status', 'unknown')}")
    
    # Wait for experiment to complete
    print("\nWaiting for experiment to complete...")
    time.sleep(3)
    
    final_status = manager.get_experiment_status("resource_exhaustion")
    print(f"Final status: {final_status}")


def demo_experiment_management():
    """Demonstrate experiment management features"""
    print("\n=== Experiment Management Demo ===")
    
    manager = ChaosExperimentManager()
    
    # List available experiments
    print("Available experiments:")
    experiments = manager.list_experiments()
    for exp in experiments['available_experiments']:
        print(f"  - {exp['name']}: {exp['description']}")
        print(f"    Parameters: {exp['parameters']}")
    
    # Start multiple experiments
    print("\nStarting multiple experiments...")
    manager.start_experiment("latency_injection", delay_seconds=1.0, duration_seconds=15.0)
    manager.start_experiment("error_injection", error_rate=0.2, duration_seconds=15.0)
    
    # List active experiments
    active = manager.list_experiments()
    print(f"\nActive experiments: {len(active['active_experiments'])}")
    for exp in active['active_experiments']:
        print(f"  - {exp['name']} (status: {exp['status']})")
    
    # Stop all experiments
    print("\nStopping all experiments...")
    for exp in active['active_experiments']:
        result = manager.stop_experiment(exp['name'])
        print(f"Stopped {exp['name']}: {result.get('status', 'unknown')}")


def main():
    """Run all demos"""
    print("Chaos Experiments Demo")
    print("=====================")
    
    try:
        demo_latency_injection()
        demo_error_injection()
        demo_resource_exhaustion()
        demo_experiment_management()
        
        print("\n=== Demo Complete ===")
        print("All chaos experiments demonstrated successfully!")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
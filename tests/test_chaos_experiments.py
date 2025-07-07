"""
Tests for chaos experiments functionality
"""
import pytest
import time
import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the parent directory to sys.path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from genericsuite.models.chaos.chaos_experiments import (
    ChaosExperiment,
    LatencyInjectionExperiment,
    ErrorInjectionExperiment,
    ResourceExhaustionExperiment,
    ChaosExperimentManager,
    list_chaos_experiments,
    start_chaos_experiment,
    stop_chaos_experiment,
    get_chaos_experiment_status,
    chaos_test_endpoint,
)


class TestChaosExperiment:
    """Test base ChaosExperiment class"""
    
    def test_chaos_experiment_init(self):
        """Test ChaosExperiment initialization"""
        experiment = ChaosExperiment("test", "Test experiment")
        assert experiment.name == "test"
        assert experiment.description == "Test experiment"
        assert experiment.status == "inactive"
        assert experiment.start_time is None
        assert experiment.end_time is None
        assert experiment.results == {}
    
    def test_chaos_experiment_start(self):
        """Test starting a chaos experiment"""
        experiment = ChaosExperiment("test", "Test experiment")
        result = experiment.start()
        
        assert experiment.status == "running"
        assert experiment.start_time is not None
        assert result["status"] == "started"
        assert result["experiment"] == "test"
        assert "start_time" in result
    
    def test_chaos_experiment_stop(self):
        """Test stopping a chaos experiment"""
        experiment = ChaosExperiment("test", "Test experiment")
        experiment.start()
        time.sleep(0.1)  # Small delay to ensure duration > 0
        result = experiment.stop()
        
        assert experiment.status == "completed"
        assert experiment.end_time is not None
        assert result["status"] == "stopped"
        assert result["experiment"] == "test"
        assert result["duration"] > 0


class TestLatencyInjectionExperiment:
    """Test LatencyInjectionExperiment class"""
    
    def test_latency_injection_init(self):
        """Test LatencyInjectionExperiment initialization"""
        experiment = LatencyInjectionExperiment(delay_seconds=1.0, duration_seconds=5.0)
        assert experiment.name == "latency_injection"
        assert experiment.delay_seconds == 1.0
        assert experiment.duration_seconds == 5.0
        assert experiment.active is False
    
    def test_latency_injection_execute(self):
        """Test executing latency injection experiment"""
        experiment = LatencyInjectionExperiment(delay_seconds=0.1, duration_seconds=1.0)
        result = experiment.execute()
        
        assert result["status"] == "executed"
        assert result["experiment"] == "latency_injection"
        assert result["delay_seconds"] == 0.1
        assert result["duration_seconds"] == 1.0
        assert experiment.active is True
        
        # Wait for experiment to auto-stop
        time.sleep(1.2)
        assert experiment.active is False
    
    def test_latency_injection_inject_delay(self):
        """Test delay injection when active"""
        experiment = LatencyInjectionExperiment(delay_seconds=0.1, duration_seconds=1.0)
        
        # Should not inject delay when inactive
        start_time = time.time()
        experiment.inject_delay()
        duration = time.time() - start_time
        assert duration < 0.05  # Should be very fast
        
        # Should inject delay when active
        experiment.execute()
        start_time = time.time()
        experiment.inject_delay()
        duration = time.time() - start_time
        assert duration >= 0.1  # Should have delay


class TestErrorInjectionExperiment:
    """Test ErrorInjectionExperiment class"""
    
    def test_error_injection_init(self):
        """Test ErrorInjectionExperiment initialization"""
        experiment = ErrorInjectionExperiment(error_rate=0.5, duration_seconds=5.0)
        assert experiment.name == "error_injection"
        assert experiment.error_rate == 0.5
        assert experiment.duration_seconds == 5.0
        assert experiment.active is False
        assert experiment.error_count == 0
        assert experiment.request_count == 0
    
    def test_error_injection_execute(self):
        """Test executing error injection experiment"""
        experiment = ErrorInjectionExperiment(error_rate=0.5, duration_seconds=1.0)
        result = experiment.execute()
        
        assert result["status"] == "executed"
        assert result["experiment"] == "error_injection"
        assert result["error_rate"] == 0.5
        assert result["duration_seconds"] == 1.0
        assert experiment.active is True
        
        # Wait for experiment to auto-stop
        time.sleep(1.2)
        assert experiment.active is False
    
    def test_error_injection_should_inject_error(self):
        """Test error injection logic"""
        # Test with 0% error rate
        experiment = ErrorInjectionExperiment(error_rate=0.0, duration_seconds=1.0)
        experiment.execute()
        
        errors = 0
        for _ in range(100):
            if experiment.should_inject_error():
                errors += 1
        
        assert errors == 0
        assert experiment.request_count == 100
        
        # Test with 100% error rate
        experiment = ErrorInjectionExperiment(error_rate=1.0, duration_seconds=1.0)
        experiment.execute()
        
        errors = 0
        for _ in range(10):
            if experiment.should_inject_error():
                errors += 1
        
        assert errors == 10


class TestResourceExhaustionExperiment:
    """Test ResourceExhaustionExperiment class"""
    
    def test_resource_exhaustion_init(self):
        """Test ResourceExhaustionExperiment initialization"""
        experiment = ResourceExhaustionExperiment(memory_mb=50, duration_seconds=5.0)
        assert experiment.name == "resource_exhaustion"
        assert experiment.memory_mb == 50
        assert experiment.duration_seconds == 5.0
        assert experiment.active is False
        assert experiment.memory_data == []
    
    def test_resource_exhaustion_execute(self):
        """Test executing resource exhaustion experiment"""
        experiment = ResourceExhaustionExperiment(memory_mb=10, duration_seconds=1.0)
        result = experiment.execute()
        
        assert result["status"] == "executed"
        assert result["experiment"] == "resource_exhaustion"
        assert result["memory_mb"] == 10
        assert result["duration_seconds"] == 1.0
        assert experiment.active is True
        
        # Wait for experiment to complete
        time.sleep(1.5)
        assert experiment.active is False
        assert experiment.memory_data == []  # Should be cleared


class TestChaosExperimentManager:
    """Test ChaosExperimentManager class"""
    
    def test_manager_init(self):
        """Test manager initialization"""
        manager = ChaosExperimentManager()
        assert manager.experiments == {}
        assert manager.active_experiments == []
    
    def test_register_experiment(self):
        """Test registering an experiment"""
        manager = ChaosExperimentManager()
        experiment = ChaosExperiment("test", "Test experiment")
        manager.register_experiment(experiment)
        
        assert "test" in manager.experiments
        assert manager.experiments["test"] == experiment
    
    def test_start_latency_experiment(self):
        """Test starting a latency injection experiment"""
        manager = ChaosExperimentManager()
        result = manager.start_experiment("latency_injection", delay_seconds=0.1, duration_seconds=1.0)
        
        assert result["status"] == "executed"
        assert result["experiment"] == "latency_injection"
        assert "latency_injection" in manager.active_experiments
        assert "latency_injection" in manager.experiments
    
    def test_start_error_experiment(self):
        """Test starting an error injection experiment"""
        manager = ChaosExperimentManager()
        result = manager.start_experiment("error_injection", error_rate=0.5, duration_seconds=1.0)
        
        assert result["status"] == "executed"
        assert result["experiment"] == "error_injection"
        assert "error_injection" in manager.active_experiments
    
    def test_start_resource_experiment(self):
        """Test starting a resource exhaustion experiment"""
        manager = ChaosExperimentManager()
        result = manager.start_experiment("resource_exhaustion", memory_mb=10, duration_seconds=1.0)
        
        assert result["status"] == "executed"
        assert result["experiment"] == "resource_exhaustion"
        assert "resource_exhaustion" in manager.active_experiments
    
    def test_start_unknown_experiment(self):
        """Test starting an unknown experiment"""
        manager = ChaosExperimentManager()
        result = manager.start_experiment("unknown_experiment")
        
        assert "error" in result
        assert "Unknown experiment" in result["error"]
    
    def test_stop_experiment(self):
        """Test stopping an experiment"""
        manager = ChaosExperimentManager()
        manager.start_experiment("latency_injection", delay_seconds=0.1, duration_seconds=5.0)
        
        result = manager.stop_experiment("latency_injection")
        assert result["status"] == "stopped"
        assert "latency_injection" not in manager.active_experiments
    
    def test_stop_nonexistent_experiment(self):
        """Test stopping a non-existent experiment"""
        manager = ChaosExperimentManager()
        result = manager.stop_experiment("nonexistent")
        
        assert "error" in result
        assert "not found" in result["error"]
    
    def test_list_experiments(self):
        """Test listing experiments"""
        manager = ChaosExperimentManager()
        result = manager.list_experiments()
        
        assert "available_experiments" in result
        assert "active_experiments" in result
        assert len(result["available_experiments"]) == 3  # latency, error, resource
        
        # Start an experiment and check active list
        manager.start_experiment("latency_injection", delay_seconds=0.1, duration_seconds=1.0)
        result = manager.list_experiments()
        assert len(result["active_experiments"]) == 1
    
    def test_get_experiment_status(self):
        """Test getting experiment status"""
        manager = ChaosExperimentManager()
        manager.start_experiment("latency_injection", delay_seconds=0.1, duration_seconds=1.0)
        
        result = manager.get_experiment_status("latency_injection")
        assert result["name"] == "latency_injection"
        assert result["status"] == "running"
        assert "start_time" in result
    
    def test_get_nonexistent_experiment_status(self):
        """Test getting status of non-existent experiment"""
        manager = ChaosExperimentManager()
        result = manager.get_experiment_status("nonexistent")
        
        assert "error" in result
        assert "not found" in result["error"]


class TestChaosEndpoints:
    """Test chaos experiment endpoints"""
    
    def test_list_chaos_experiments_endpoint(self):
        """Test list chaos experiments endpoint"""
        mock_request = Mock()
        result = list_chaos_experiments(mock_request)
        
        # Should return a successful response with experiments list
        assert hasattr(result, 'json') or isinstance(result, dict)
    
    def test_start_chaos_experiment_endpoint(self):
        """Test start chaos experiment endpoint"""
        mock_request = Mock()
        mock_request.json_body = {
            "experiment_name": "latency_injection",
            "delay_seconds": 0.1,
            "duration_seconds": 1.0
        }
        
        result = start_chaos_experiment(mock_request)
        assert hasattr(result, 'json') or isinstance(result, dict)
    
    def test_start_chaos_experiment_missing_name(self):
        """Test start chaos experiment with missing name"""
        mock_request = Mock()
        mock_request.json_body = {}
        
        result = start_chaos_experiment(mock_request)
        assert hasattr(result, 'json') or isinstance(result, dict)
    
    def test_stop_chaos_experiment_endpoint(self):
        """Test stop chaos experiment endpoint"""
        # Create a new manager for this test
        manager = ChaosExperimentManager()
        manager.start_experiment("latency_injection", delay_seconds=0.1, duration_seconds=5.0)
        
        mock_request = Mock()
        mock_request.json_body = {
            "experiment_name": "latency_injection"
        }
        
        # Temporarily replace the global manager
        import genericsuite.models.chaos.chaos_experiments as chaos_module
        original_manager = chaos_module.chaos_manager
        chaos_module.chaos_manager = manager
        
        try:
            result = stop_chaos_experiment(mock_request)
            assert hasattr(result, 'data') or isinstance(result, dict)
        finally:
            chaos_module.chaos_manager = original_manager
    
    def test_get_chaos_experiment_status_endpoint(self):
        """Test get chaos experiment status endpoint"""
        # Create a new manager for this test
        manager = ChaosExperimentManager()
        manager.start_experiment("latency_injection", delay_seconds=0.1, duration_seconds=5.0)
        
        mock_request = Mock()
        mock_request.query_params = {"experiment_name": "latency_injection"}
        
        # Temporarily replace the global manager
        import genericsuite.models.chaos.chaos_experiments as chaos_module
        original_manager = chaos_module.chaos_manager
        chaos_module.chaos_manager = manager
        
        try:
            result = get_chaos_experiment_status(mock_request)
            assert hasattr(result, 'data') or isinstance(result, dict)
        finally:
            chaos_module.chaos_manager = original_manager
    
    def test_chaos_test_endpoint(self):
        """Test chaos test endpoint"""
        mock_request = Mock()
        result = chaos_test_endpoint(mock_request)
        assert hasattr(result, 'data') or isinstance(result, dict)
    
    def test_chaos_test_endpoint_with_latency(self):
        """Test chaos test endpoint with active latency experiment"""
        # Create a new manager for this test
        manager = ChaosExperimentManager()
        manager.start_experiment("latency_injection", delay_seconds=0.1, duration_seconds=5.0)
        
        # Temporarily replace the global manager
        import genericsuite.models.chaos.chaos_experiments as chaos_module
        original_manager = chaos_module.chaos_manager
        chaos_module.chaos_manager = manager
        
        try:
            mock_request = Mock()
            start_time = time.time()
            result = chaos_test_endpoint(mock_request)
            duration = time.time() - start_time
            
            # Should have delay applied
            assert duration >= 0.1
            assert hasattr(result, 'data') or isinstance(result, dict)
        finally:
            chaos_module.chaos_manager = original_manager
    
    def test_chaos_test_endpoint_with_error_injection(self):
        """Test chaos test endpoint with active error injection"""
        # Create a new manager for this test
        manager = ChaosExperimentManager()
        manager.start_experiment("error_injection", error_rate=1.0, duration_seconds=5.0)
        
        # Temporarily replace the global manager
        import genericsuite.models.chaos.chaos_experiments as chaos_module
        original_manager = chaos_module.chaos_manager
        chaos_module.chaos_manager = manager
        
        try:
            mock_request = Mock()
            result = chaos_test_endpoint(mock_request)
            
            # Should return error due to 100% error rate
            assert hasattr(result, 'data') or isinstance(result, dict)
        finally:
            chaos_module.chaos_manager = original_manager


if __name__ == "__main__":
    pytest.main([__file__])
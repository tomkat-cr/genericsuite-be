"""
Chaos experiments operations and utilities
"""
import time
import random
import threading
from typing import Optional, Dict, Any, List
from datetime import datetime

# Simple mock functions to avoid dependency issues during testing
def log_debug(msg):
    """Simple debug logger"""
    pass

def log_info(msg):
    """Simple info logger"""
    pass

def get_default_resultset():
    """Get default result set"""
    return {'error': False, 'resultset': {}}

def error_resultset(msg):
    """Get error result set"""
    return {'error': True, 'error_message': msg}

def return_resultset_jsonified_or_exception(result):
    """Return result as is for testing"""
    return result

# Import framework abstractions if available, otherwise use simple mocks
try:
    import os
    if not os.environ.get('CURRENT_FRAMEWORK'):
        os.environ['CURRENT_FRAMEWORK'] = 'flask'  # Default for testing
    from genericsuite.util.framework_abs_layer import Request, Response
except (ImportError, ValueError):
    # Mock for testing
    class Request:
        def __init__(self):
            self.json_body = {}
            self.json = {}
            self.query_params = {}
            self.args = {}
    
    class Response:
        def __init__(self, data):
            self.data = data

DEBUG = False


class ChaosExperiment:
    """Base class for chaos experiments"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.start_time = None
        self.end_time = None
        self.status = "inactive"
        self.results = {}
    
    def start(self) -> Dict[str, Any]:
        """Start the chaos experiment"""
        self.start_time = datetime.now()
        self.status = "running"
        return {"status": "started", "experiment": self.name, "start_time": self.start_time.isoformat()}
    
    def stop(self) -> Dict[str, Any]:
        """Stop the chaos experiment"""
        self.end_time = datetime.now()
        self.status = "completed"
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0
        return {
            "status": "stopped", 
            "experiment": self.name, 
            "duration": duration,
            "results": self.results
        }
    
    def execute(self) -> Dict[str, Any]:
        """Execute the chaos experiment - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement execute method")


class LatencyInjectionExperiment(ChaosExperiment):
    """Experiment that introduces artificial latency"""
    
    def __init__(self, delay_seconds: float = 2.0, duration_seconds: float = 30.0):
        super().__init__(
            "latency_injection",
            f"Introduces {delay_seconds}s delay for {duration_seconds}s"
        )
        self.delay_seconds = delay_seconds
        self.duration_seconds = duration_seconds
        self.active = False
    
    def execute(self) -> Dict[str, Any]:
        """Execute latency injection"""
        self.start()
        self.active = True
        
        def stop_after_duration():
            time.sleep(self.duration_seconds)
            self.active = False
            self.stop()
        
        # Start timer to stop experiment
        timer_thread = threading.Thread(target=stop_after_duration)
        timer_thread.daemon = True
        timer_thread.start()
        
        return {
            "status": "executed",
            "experiment": self.name,
            "delay_seconds": self.delay_seconds,
            "duration_seconds": self.duration_seconds
        }
    
    def inject_delay(self):
        """Apply delay if experiment is active"""
        if self.active:
            time.sleep(self.delay_seconds)


class ErrorInjectionExperiment(ChaosExperiment):
    """Experiment that introduces random errors"""
    
    def __init__(self, error_rate: float = 0.1, duration_seconds: float = 30.0):
        super().__init__(
            "error_injection",
            f"Introduces {error_rate*100}% error rate for {duration_seconds}s"
        )
        self.error_rate = error_rate
        self.duration_seconds = duration_seconds
        self.active = False
        self.error_count = 0
        self.request_count = 0
    
    def execute(self) -> Dict[str, Any]:
        """Execute error injection"""
        self.start()
        self.active = True
        self.error_count = 0
        self.request_count = 0
        
        def stop_after_duration():
            time.sleep(self.duration_seconds)
            self.active = False
            self.results = {
                "total_requests": self.request_count,
                "errors_injected": self.error_count,
                "actual_error_rate": self.error_count / max(self.request_count, 1)
            }
            self.stop()
        
        # Start timer to stop experiment
        timer_thread = threading.Thread(target=stop_after_duration)
        timer_thread.daemon = True
        timer_thread.start()
        
        return {
            "status": "executed",
            "experiment": self.name,
            "error_rate": self.error_rate,
            "duration_seconds": self.duration_seconds
        }
    
    def should_inject_error(self) -> bool:
        """Check if an error should be injected"""
        if not self.active:
            return False
        
        self.request_count += 1
        should_error = random.random() < self.error_rate
        
        if should_error:
            self.error_count += 1
        
        return should_error


class ResourceExhaustionExperiment(ChaosExperiment):
    """Experiment that exhausts system resources"""
    
    def __init__(self, memory_mb: int = 100, duration_seconds: float = 30.0):
        super().__init__(
            "resource_exhaustion",
            f"Consumes {memory_mb}MB memory for {duration_seconds}s"
        )
        self.memory_mb = memory_mb
        self.duration_seconds = duration_seconds
        self.memory_data = []
        self.active = False
    
    def execute(self) -> Dict[str, Any]:
        """Execute resource exhaustion"""
        self.start()
        self.active = True
        
        def consume_memory_and_stop():
            # Consume memory
            try:
                # Allocate memory (roughly 1MB per list of 250k integers)
                for _ in range(self.memory_mb):
                    self.memory_data.append([0] * 250000)
                
                # Hold memory for duration
                time.sleep(self.duration_seconds)
                
            finally:
                # Release memory
                self.memory_data.clear()
                self.active = False
                self.results = {
                    "memory_consumed_mb": self.memory_mb,
                    "duration_seconds": self.duration_seconds
                }
                self.stop()
        
        # Start memory consumption in separate thread
        memory_thread = threading.Thread(target=consume_memory_and_stop)
        memory_thread.daemon = True
        memory_thread.start()
        
        return {
            "status": "executed",
            "experiment": self.name,
            "memory_mb": self.memory_mb,
            "duration_seconds": self.duration_seconds
        }


class ChaosExperimentManager:
    """Manager for chaos experiments"""
    
    def __init__(self):
        self.experiments: Dict[str, ChaosExperiment] = {}
        self.active_experiments: List[str] = []
    
    def register_experiment(self, experiment: ChaosExperiment):
        """Register a new experiment"""
        self.experiments[experiment.name] = experiment
    
    def start_experiment(self, experiment_name: str, **kwargs) -> Dict[str, Any]:
        """Start a specific experiment"""
        if experiment_name == "latency_injection":
            experiment = LatencyInjectionExperiment(
                delay_seconds=kwargs.get("delay_seconds", 2.0),
                duration_seconds=kwargs.get("duration_seconds", 30.0)
            )
        elif experiment_name == "error_injection":
            experiment = ErrorInjectionExperiment(
                error_rate=kwargs.get("error_rate", 0.1),
                duration_seconds=kwargs.get("duration_seconds", 30.0)
            )
        elif experiment_name == "resource_exhaustion":
            experiment = ResourceExhaustionExperiment(
                memory_mb=kwargs.get("memory_mb", 100),
                duration_seconds=kwargs.get("duration_seconds", 30.0)
            )
        else:
            return {"error": f"Unknown experiment: {experiment_name}"}
        
        self.register_experiment(experiment)
        result = experiment.execute()
        
        if experiment_name not in self.active_experiments:
            self.active_experiments.append(experiment_name)
        
        return result
    
    def stop_experiment(self, experiment_name: str) -> Dict[str, Any]:
        """Stop a specific experiment"""
        if experiment_name not in self.experiments:
            return {"error": f"Experiment {experiment_name} not found"}
        
        experiment = self.experiments[experiment_name]
        result = experiment.stop()
        
        if experiment_name in self.active_experiments:
            self.active_experiments.remove(experiment_name)
        
        return result
    
    def list_experiments(self) -> Dict[str, Any]:
        """List all available experiments"""
        available_experiments = [
            {
                "name": "latency_injection",
                "description": "Introduces artificial latency to responses",
                "parameters": ["delay_seconds", "duration_seconds"]
            },
            {
                "name": "error_injection",
                "description": "Randomly injects errors into responses",
                "parameters": ["error_rate", "duration_seconds"]
            },
            {
                "name": "resource_exhaustion",
                "description": "Consumes system resources (memory)",
                "parameters": ["memory_mb", "duration_seconds"]
            }
        ]
        
        active_experiments = []
        for exp_name in self.active_experiments:
            if exp_name in self.experiments:
                exp = self.experiments[exp_name]
                active_experiments.append({
                    "name": exp_name,
                    "status": exp.status,
                    "start_time": exp.start_time.isoformat() if exp.start_time else None
                })
        
        return {
            "available_experiments": available_experiments,
            "active_experiments": active_experiments
        }
    
    def get_experiment_status(self, experiment_name: str) -> Dict[str, Any]:
        """Get status of a specific experiment"""
        if experiment_name not in self.experiments:
            return {"error": f"Experiment {experiment_name} not found"}
        
        experiment = self.experiments[experiment_name]
        return {
            "name": experiment.name,
            "description": experiment.description,
            "status": experiment.status,
            "start_time": experiment.start_time.isoformat() if experiment.start_time else None,
            "end_time": experiment.end_time.isoformat() if experiment.end_time else None,
            "results": experiment.results
        }


# Global manager instance
chaos_manager = ChaosExperimentManager()


def list_chaos_experiments(
    request: Request,
    blueprint=None,
    other_params: Optional[dict] = None
) -> Response:
    """List all available chaos experiments"""
    _ = DEBUG and log_debug("LIST_CHAOS_EXPERIMENTS | Starting...")
    
    try:
        result = get_default_resultset()
        experiments_data = chaos_manager.list_experiments()
        result['resultset'] = experiments_data
        
        _ = DEBUG and log_debug(f"LIST_CHAOS_EXPERIMENTS | Result: {result}")
        
    except Exception as e:
        error_msg = f"LIST_CHAOS_EXPERIMENTS | Error: {str(e)}"
        log_info(error_msg)
        result = error_resultset(error_msg)
    
    return return_resultset_jsonified_or_exception(result)


def start_chaos_experiment(
    request: Request,
    blueprint=None,
    other_params: Optional[dict] = None
) -> Response:
    """Start a chaos experiment"""
    _ = DEBUG and log_debug("START_CHAOS_EXPERIMENT | Starting...")
    
    try:
        # Get experiment parameters from request
        if hasattr(request, 'json_body') and request.json_body:
            experiment_data = request.json_body
        elif hasattr(request, 'json') and request.json:
            experiment_data = request.json
        else:
            experiment_data = {}
        
        experiment_name = experiment_data.get('experiment_name')
        if not experiment_name:
            result = error_resultset("Missing required parameter: experiment_name")
            return return_resultset_jsonified_or_exception(result)
        
        # Extract experiment parameters
        experiment_params = {
            key: value for key, value in experiment_data.items() 
            if key != 'experiment_name'
        }
        
        result = get_default_resultset()
        experiment_result = chaos_manager.start_experiment(experiment_name, **experiment_params)
        
        if 'error' in experiment_result:
            result = error_resultset(experiment_result['error'])
        else:
            result['resultset'] = experiment_result
        
        _ = DEBUG and log_debug(f"START_CHAOS_EXPERIMENT | Result: {result}")
        
    except Exception as e:
        error_msg = f"START_CHAOS_EXPERIMENT | Error: {str(e)}"
        log_info(error_msg)
        result = error_resultset(error_msg)
    
    return return_resultset_jsonified_or_exception(result)


def stop_chaos_experiment(
    request: Request,
    blueprint=None,
    other_params: Optional[dict] = None
) -> Response:
    """Stop a chaos experiment"""
    _ = DEBUG and log_debug("STOP_CHAOS_EXPERIMENT | Starting...")
    
    try:
        # Get experiment name from request
        if hasattr(request, 'json_body') and request.json_body:
            experiment_data = request.json_body
        elif hasattr(request, 'json') and request.json:
            experiment_data = request.json
        else:
            experiment_data = {}
        
        experiment_name = experiment_data.get('experiment_name')
        if not experiment_name:
            result = error_resultset("Missing required parameter: experiment_name")
            return return_resultset_jsonified_or_exception(result)
        
        result = get_default_resultset()
        experiment_result = chaos_manager.stop_experiment(experiment_name)
        
        if 'error' in experiment_result:
            result = error_resultset(experiment_result['error'])
        else:
            result['resultset'] = experiment_result
        
        _ = DEBUG and log_debug(f"STOP_CHAOS_EXPERIMENT | Result: {result}")
        
    except Exception as e:
        error_msg = f"STOP_CHAOS_EXPERIMENT | Error: {str(e)}"
        log_info(error_msg)
        result = error_resultset(error_msg)
    
    return return_resultset_jsonified_or_exception(result)


def get_chaos_experiment_status(
    request: Request,
    blueprint=None,
    other_params: Optional[dict] = None
) -> Response:
    """Get status of a chaos experiment"""
    _ = DEBUG and log_debug("GET_CHAOS_EXPERIMENT_STATUS | Starting...")
    
    try:
        # Get experiment name from URL params or query string
        experiment_name = None
        
        # Try to get from query parameters
        if hasattr(request, 'query_params') and request.query_params:
            experiment_name = request.query_params.get('experiment_name')
        elif hasattr(request, 'args') and request.args:
            experiment_name = request.args.get('experiment_name')
        
        # Try to get from path parameters (if passed via other_params)
        if not experiment_name and other_params:
            experiment_name = other_params.get('experiment_name')
        
        if not experiment_name:
            result = error_resultset("Missing required parameter: experiment_name")
            return return_resultset_jsonified_or_exception(result)
        
        result = get_default_resultset()
        experiment_result = chaos_manager.get_experiment_status(experiment_name)
        
        if 'error' in experiment_result:
            result = error_resultset(experiment_result['error'])
        else:
            result['resultset'] = experiment_result
        
        _ = DEBUG and log_debug(f"GET_CHAOS_EXPERIMENT_STATUS | Result: {result}")
        
    except Exception as e:
        error_msg = f"GET_CHAOS_EXPERIMENT_STATUS | Error: {str(e)}"
        log_info(error_msg)
        result = error_resultset(error_msg)
    
    return return_resultset_jsonified_or_exception(result)


def chaos_test_endpoint(
    request: Request,
    blueprint=None,
    other_params: Optional[dict] = None
) -> Response:
    """Test endpoint that applies active chaos experiments"""
    _ = DEBUG and log_debug("CHAOS_TEST_ENDPOINT | Starting...")
    
    try:
        # Apply chaos experiments if active
        for exp_name in chaos_manager.active_experiments:
            if exp_name in chaos_manager.experiments:
                experiment = chaos_manager.experiments[exp_name]
                
                # Apply latency injection
                if isinstance(experiment, LatencyInjectionExperiment):
                    experiment.inject_delay()
                
                # Apply error injection
                elif isinstance(experiment, ErrorInjectionExperiment):
                    if experiment.should_inject_error():
                        result = error_resultset("Chaos experiment: Injected error")
                        return return_resultset_jsonified_or_exception(result)
        
        # Normal response if no chaos applied
        result = get_default_resultset()
        result['resultset'] = {
            "message": "Test endpoint response",
            "timestamp": datetime.now().isoformat(),
            "active_chaos_experiments": chaos_manager.active_experiments
        }
        
        _ = DEBUG and log_debug(f"CHAOS_TEST_ENDPOINT | Result: {result}")
        
    except Exception as e:
        error_msg = f"CHAOS_TEST_ENDPOINT | Error: {str(e)}"
        log_info(error_msg)
        result = error_resultset(error_msg)
    
    return return_resultset_jsonified_or_exception(result)
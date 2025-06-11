import subprocess
import time
import json
import os
from datetime import datetime
import signal
import sys
from pathlib import Path

class ThroughputLogger:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": []
        }
        self.current_test = None

    def start_test(self, transmitter, file_name, scenario):
        self.current_test = {
            "transmitter": transmitter,
            "file_name": file_name,
            "scenario": scenario,
            "runs": []
        }

    def log_run(self, run_number, file_size, duration, throughput, scenario):
        self.current_test["runs"].append({
            "run": run_number,
            "timestamp": datetime.now().isoformat(),
            "file_size_bytes": file_size,
            "duration_seconds": duration,
            "throughput_bytes_per_second": throughput,
            "throughput_kb_per_second": throughput/1024,
            "scenario": scenario
        })

    def end_test(self):
        if self.current_test:
            # Calculate averages
            runs = self.current_test["runs"]
            self.current_test["average_duration"] = sum(r["duration_seconds"] for r in runs) / len(runs)
            self.current_test["average_throughput"] = sum(r["throughput_bytes_per_second"] for r in runs) / len(runs)
            self.current_test["min_throughput"] = min(r["throughput_bytes_per_second"] for r in runs)
            self.current_test["max_throughput"] = max(r["throughput_bytes_per_second"] for r in runs)
            
            self.results["tests"].append(self.current_test)
            self.current_test = None

    def save_results(self):
        # Create results directory if it doesn't exist
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        # Save with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = results_dir / f"transmitter_results_{timestamp}.txt"
        
        with open(output_file, 'w') as f:
            f.write("TRANSMITTER TEST RESULTS\n")
            f.write("=" * 50 + "\n\n")
            
            for test in self.results["tests"]:
                f.write(f"Test Case: {test['transmitter'].upper()} transmitter\n")
                f.write(f"File: {test['file_name']}\n")
                f.write(f"Scenario: {test['scenario']}\n")
                f.write("-" * 30 + "\n")
                
                # Write individual run results
                for run in test["runs"]:
                    f.write(f"Run {run['run']}:\n")
                    f.write(f"  Duration: {run['duration_seconds']:.2f} seconds\n")
                    f.write(f"  Throughput: {run['throughput_kb_per_second']:.2f} KB/s\n")
                    f.write(f"  File Size: {run['file_size_bytes']/1024:.2f} KB\n")
                    f.write("\n")
                
                # Write summary statistics
                f.write("Summary Statistics:\n")
                f.write(f"  Average Duration: {test['average_duration']:.2f} seconds\n")
                f.write(f"  Average Throughput: {test['average_throughput']/1024:.2f} KB/s\n")
                f.write(f"  Min Throughput: {test['min_throughput']/1024:.2f} KB/s\n")
                f.write(f"  Max Throughput: {test['max_throughput']/1024:.2f} KB/s\n")
                f.write("\n" + "=" * 50 + "\n\n")
        
        print(f"\nResults saved to: {output_file}")

class ThroughputTester:
    def __init__(self):
        self.logger = ThroughputLogger()
        self.test_files = ["test_data.txt", "image.png"]
        # Only test transmitters
        self.transmitters = ["python", "go"]
        # Hardcoded IP address - change this as needed
        self.remote_ip = "127.0.0.1"  # Change this to your friend's IP
        # Test scenarios
        self.scenarios = [
            {"name": "Normal", "timeout": 1.0},
            {"name": "Quick Timeout", "timeout": 0.1},  # Simulate network issues
            {"name": "Very Quick Timeout", "timeout": 0.01}  # Simulate severe network issues
        ]

    def run_transmitter(self, transmitter_type, file_name, timeout):
        if transmitter_type == "python":
            # Set environment variable for timeout
            env = os.environ.copy()
            env["UDP_TIMEOUT"] = str(timeout)
            subprocess.run(["python", "Python/transmitter.py", file_name, self.remote_ip], env=env)
        else:  # go
            env = os.environ.copy()
            env["UDP_TIMEOUT"] = str(timeout)
            subprocess.run(["go", "run", "Go/cmd/udp/main.go", file_name, self.remote_ip], env=env)

    def get_file_size(self, file_name):
        return os.path.getsize(file_name)

    def run_test(self, transmitter, file_name, run_number, scenario):
        print(f"\n{'='*50}")
        print(f"Test Case: {transmitter.upper()} transmitter")
        print(f"File: {file_name}")
        print(f"Scenario: {scenario['name']} (timeout: {scenario['timeout']}s)")
        print(f"Run {run_number}/10")
        print(f"{'='*50}")
        
        # Get file size
        file_size = self.get_file_size(file_name)
        
        # Run transmitter and measure time
        start_time = time.time()
        self.run_transmitter(transmitter, file_name, scenario['timeout'])
        end_time = time.time()
        
        # Calculate metrics
        duration = end_time - start_time
        throughput = file_size / duration
        
        # Log results
        self.logger.log_run(run_number, file_size, duration, throughput, scenario['name'])
        
        print(f"Duration: {duration:.2f}s")
        print(f"Throughput: {throughput/1024:.2f} KB/s")
        print(f"{'='*50}\n")

    def run_all_tests(self):
        try:
            for transmitter in self.transmitters:
                for file_name in self.test_files:
                    for scenario in self.scenarios:
                        print(f"\n=== Testing {transmitter.upper()} transmitter ===")
                        print(f"File: {file_name}")
                        print(f"Scenario: {scenario['name']}")
                        
                        self.logger.start_test(transmitter, file_name, scenario['name'])
                        
                        for run in range(1, 11):
                            self.run_test(transmitter, file_name, run, scenario)
                        
                        self.logger.end_test()
                        
                        # Small pause between tests
                        time.sleep(1)
            
            self.logger.save_results()
            
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
        except Exception as e:
            print(f"\nError during testing: {e}")

def main():
    tester = ThroughputTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 
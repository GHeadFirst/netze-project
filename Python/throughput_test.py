import subprocess
import time
import json
import os
from datetime import datetime
import signal
import sys
from pathlib import Path
import argparse

class ThroughputLogger:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": []
        }
        self.current_test = None

    def start_test(self, transmitter, receiver, file_name, is_remote=False):
        self.current_test = {
            "transmitter": transmitter,
            "receiver": receiver,
            "file_name": file_name,
            "is_remote": is_remote,
            "runs": []
        }

    def log_run(self, run_number, file_size, duration, throughput, acks_received, retries):
        self.current_test["runs"].append({
            "run": run_number,
            "timestamp": datetime.now().isoformat(),
            "file_size_bytes": file_size,
            "duration_seconds": duration,
            "throughput_bytes_per_second": throughput,
            "throughput_kb_per_second": throughput/1024,
            "acks_received": acks_received,
            "retries": retries,
            "success_rate": (acks_received / (acks_received + retries)) * 100 if (acks_received + retries) > 0 else 0
        })

    def end_test(self):
        if self.current_test:
            # Calculate averages
            runs = self.current_test["runs"]
            self.current_test["average_duration"] = sum(r["duration_seconds"] for r in runs) / len(runs)
            self.current_test["average_throughput"] = sum(r["throughput_bytes_per_second"] for r in runs) / len(runs)
            self.current_test["min_throughput"] = min(r["throughput_bytes_per_second"] for r in runs)
            self.current_test["max_throughput"] = max(r["throughput_bytes_per_second"] for r in runs)
            self.current_test["average_success_rate"] = sum(r["success_rate"] for r in runs) / len(runs)
            self.current_test["total_acks"] = sum(r["acks_received"] for r in runs)
            self.current_test["total_retries"] = sum(r["retries"] for r in runs)
            
            self.results["tests"].append(self.current_test)
            self.current_test = None

    def save_results(self):
        # Create results directory if it doesn't exist
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        # Save with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = results_dir / f"throughput_results_{timestamp}.txt"
        
        with open(output_file, 'w') as f:
            f.write("THROUGHPUT TEST RESULTS\n")
            f.write("=" * 50 + "\n\n")
            
            for test in self.results["tests"]:
                f.write(f"Test Case: {test['transmitter'].upper()} transmitter -> {test['receiver'].upper()} receiver\n")
                f.write(f"File: {test['file_name']}\n")
                f.write(f"Mode: {'Remote' if test['is_remote'] else 'Local'}\n")
                f.write("-" * 30 + "\n")
                
                # Write individual run results
                for run in test["runs"]:
                    f.write(f"Run {run['run']}:\n")
                    f.write(f"  Duration: {run['duration_seconds']:.2f} seconds\n")
                    f.write(f"  Throughput: {run['throughput_kb_per_second']:.2f} KB/s\n")
                    f.write(f"  File Size: {run['file_size_bytes']/1024:.2f} KB\n")
                    f.write(f"  ACKs Received: {run['acks_received']}\n")
                    f.write(f"  Retries: {run['retries']}\n")
                    f.write(f"  Success Rate: {run['success_rate']:.1f}%\n")
                    f.write("\n")
                
                # Write summary statistics
                f.write("Summary Statistics:\n")
                f.write(f"  Average Duration: {test['average_duration']:.2f} seconds\n")
                f.write(f"  Average Throughput: {test['average_throughput']/1024:.2f} KB/s\n")
                f.write(f"  Min Throughput: {test['min_throughput']/1024:.2f} KB/s\n")
                f.write(f"  Max Throughput: {test['max_throughput']/1024:.2f} KB/s\n")
                f.write(f"  Average Success Rate: {test['average_success_rate']:.1f}%\n")
                f.write(f"  Total ACKs: {test['total_acks']}\n")
                f.write(f"  Total Retries: {test['total_retries']}\n")
                f.write("\n" + "=" * 50 + "\n\n")
        
        print(f"\nResults saved to: {output_file}")

class ThroughputTester:
    def __init__(self, remote_ip=None):
        self.logger = ThroughputLogger()
        self.test_files = ["test_50mb.bin"]  # Using smaller file for testing
        self.transmitters = ["python", "go"]
        self.receivers = ["python", "go"]
        self.remote_ip = remote_ip or "127.0.0.1"
        self.is_remote = remote_ip is not None
        self.receiver_process = None

    def start_receiver(self, receiver_type):
        """Start the receiver process"""
        if receiver_type == "python":
            self.receiver_process = subprocess.Popen(
                ["python", "Python/receiver.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        else:  # go
            self.receiver_process = subprocess.Popen(
                ["go", "run", "Go/cmd/udp/main.go", "--receiver"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        # Give the receiver time to start
        time.sleep(2)

    def stop_receiver(self):
        """Stop the receiver process"""
        if self.receiver_process:
            self.receiver_process.terminate()
            self.receiver_process.wait()
            self.receiver_process = None

    def run_transmitter(self, transmitter_type, file_name):
        """Run transmitter and capture its output"""
        if transmitter_type == "python":
            process = subprocess.run(
                ["python", "Python/transmitter.py", file_name, self.remote_ip],
                capture_output=True,
                text=True
            )
        else:  # go
            process = subprocess.run(
                ["go", "run", "Go/cmd/udp/main.go", file_name, self.remote_ip],
                capture_output=True,
                text=True
            )
        return process.stdout

    def parse_transmitter_stats(self, output):
        """Parse transmitter statistics from output"""
        acks_received = 0
        retries = 0
        for line in output.split('\n'):
            if "Total ACKs received:" in line:
                acks_received = int(line.split(':')[1].strip())
            elif "Total retries needed:" in line:
                retries = int(line.split(':')[1].strip())
        return acks_received, retries

    def parse_receiver_stats(self, output):
        """Parse receiver statistics from output"""
        acks_sent = 0
        for line in output.split('\n'):
            if "Total ACKs sent:" in line:
                acks_sent = int(line.split(':')[1].strip())
        return acks_sent

    def get_file_size(self, file_name):
        return os.path.getsize(file_name)

    def run_test(self, transmitter, receiver, file_name, run_number):
        print(f"\n{'='*50}")
        print(f"Test Case: {transmitter.upper()} transmitter -> {receiver.upper()} receiver")
        print(f"File: {file_name}")
        print(f"Mode: {'Remote' if self.is_remote else 'Local'}")
        print(f"Run {run_number}/10")
        print(f"{'='*50}")
        
        # Start receiver
        self.start_receiver(receiver)
        
        try:
            # Get file size
            file_size = self.get_file_size(file_name)
            
            # Run transmitter and measure time
            start_time = time.time()
            transmitter_output = self.run_transmitter(transmitter, file_name)
            end_time = time.time()
            
            # Calculate metrics
            duration = end_time - start_time
            throughput = file_size / duration
            
            # Parse statistics
            acks_received, retries = self.parse_transmitter_stats(transmitter_output)
            
            # Log results
            self.logger.log_run(run_number, file_size, duration, throughput, acks_received, retries)
            
            print(f"Duration: {duration:.2f}s")
            print(f"Throughput: {throughput/1024:.2f} KB/s")
            print(f"ACKs Received: {acks_received}")
            print(f"Retries: {retries}")
            print(f"{'='*50}\n")
            
        finally:
            # Always stop the receiver
            self.stop_receiver()

    def run_all_tests(self):
        try:
            for transmitter in self.transmitters:
                for receiver in self.receivers:
                    for file_name in self.test_files:
                        print(f"\n=== Testing {transmitter.upper()} -> {receiver.upper()} ===")
                        print(f"File: {file_name}")
                        print(f"Mode: {'Remote' if self.is_remote else 'Local'}")
                        
                        self.logger.start_test(transmitter, receiver, file_name, self.is_remote)
                        
                        for run in range(1, 11):
                            self.run_test(transmitter, receiver, file_name, run)
                        
                        self.logger.end_test()
                        
                        # Small pause between tests
                        time.sleep(1)
            
            self.logger.save_results()
            
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
            self.stop_receiver()
        except Exception as e:
            print(f"\nError during testing: {e}")
            self.stop_receiver()

def main():
    parser = argparse.ArgumentParser(description='Run throughput tests')
    parser.add_argument('--remote', help='Remote IP address for testing')
    args = parser.parse_args()
    
    tester = ThroughputTester(args.remote)
    tester.run_all_tests()

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
import time
import socket
import logging
from logging.handlers import TimedRotatingFileHandler

# ---------------------------
# Configuration
# ---------------------------
# List of servers to test.
# Each entry is a dictionary with "host" and optional "port" (default is 80)
SERVERS = [
    {"host": "google.com", "port": 80},
    {"host": "yahoo.com", "port": 80},
    {"host": "8.8.8.8", "port": 53},
    {"host": "192.168.1.101", "port": 3306},
    # Add more servers as needed
]

# How long (in seconds) to perform latency measurements per server.
MEASUREMENT_DURATION = 10
# Delay (in seconds) between individual connection attempts.
INTERVAL = 2

# Log filename (rotated daily)
LOG_FILENAME = "latency.log"

# ---------------------------
# Logger Setup (Daily Rotation)
# ---------------------------
logger = logging.getLogger("LatencyLogger")
logger.setLevel(logging.INFO)
handler = TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=7)
# The formatter will add a timestamp automatically.
formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

# ---------------------------
# Latency Measurement Function
# ---------------------------
def measure_latency(host, port, duration=MEASUREMENT_DURATION, interval=INTERVAL):
    """
    Measures latency to the given host:port over the specified duration.
    Uses a TCP connect (which works even if ICMP is blocked) and takes multiple samples.
    
    Returns a dict containing:
      - total_samples: total number of connection attempts
      - success_count: number of successful connections
      - fail_count: number of failed attempts
      - avg_latency: average latency in ms (if any successes), else None
      - min_latency: minimum latency in ms (if any successes), else None
      - max_latency: maximum latency in ms (if any successes), else None
      - samples: list of individual sample results (in ms) or "fail" for failures
    """
    samples = []
    success_count = 0
    fail_count = 0
    end_time = time.time() + duration

    while time.time() < end_time:
        start = time.time()
        try:
            # Attempt a TCP connection (timeout=2 sec)
            with socket.create_connection((host, port), timeout=2) as sock:
                # Connection succeeded, measure round-trip time.
                latency_ms = (time.time() - start) * 1000.0
                samples.append(latency_ms)
                success_count += 1
        except Exception:
            # On exception, record a failure.
            samples.append("fail")
            fail_count += 1
        time.sleep(interval)

    # Compute statistics over the successful measurements.
    valid_samples = [s for s in samples if isinstance(s, (float, int))]
    if valid_samples:
        avg_latency = sum(valid_samples) / len(valid_samples)
        min_latency = min(valid_samples)
        max_latency = max(valid_samples)
    else:
        avg_latency = min_latency = max_latency = None

    return {
        "total_samples": len(samples),
        "success_count": success_count,
        "fail_count": fail_count,
        "avg_latency": avg_latency,
        "min_latency": min_latency,
        "max_latency": max_latency,
        "samples": samples
    }

# ---------------------------
# Main Routine
# ---------------------------
def main():
    # Try to read the host VM's hostname from the mounted file.
    try:
        with open("/host_hostname", "r") as f:
            host_vm = f.read().strip()
    except Exception:
        host_vm = socket.gethostname()  # fallback if not mounted

    # List to hold each row's key=value strings.
    rows = []
    for server in SERVERS:
        host = server.get("host")
        port = server.get("port", 80)
        result = measure_latency(host, port)

        # Create a dictionary of key=value strings.
        row = {
            "source": f"source={host_vm}",
            "host": f"host={host}",
            "port": f"port={port}",
            "total_samples": f"total_samples={result['total_samples']}",
            "success_count": f"success_count={result['success_count']}",
            "fail_count": f"fail_count={result['fail_count']}",
        }

        if result['avg_latency'] is not None:
            row["avg_latency"] = f"avg_latency={result['avg_latency']:.2f}ms"
            row["min_latency"] = f"min_latency={result['min_latency']:.2f}ms"
            row["max_latency"] = f"max_latency={result['max_latency']:.2f}ms"
        else:
            row["avg_latency"] = "avg_latency=N/A"
            row["min_latency"] = "min_latency=N/A"
            row["max_latency"] = "max_latency=N/A"

        # Format the samples as a semicolon-separated string.
        row["samples"] = "samples=" + ";".join(
            f"{s:.2f}" if isinstance(s, (float, int)) else "fail" for s in result["samples"]
        )

        rows.append(row)

    # List of keys in the order you want them to appear in the log.
    fields = [
        "source",
        "host",
        "port",
        "total_samples",
        "success_count",
        "fail_count",
        "avg_latency",
        "min_latency",
        "max_latency",
        "samples",
    ]

    # Compute the maximum width for each column based on the longest string among the rows plus one.
    widths = {
        field: max(len(row[field]) for row in rows) + 1
        for field in fields
    }

    # Log each row with dynamically computed fixed-width columns.
    for row in rows:
        log_line = " ".join(f"{row[field]:<{widths[field]}}" for field in fields)
        logger.info(log_line)

if __name__ == "__main__":
    main()

"""
Purpose: Read all URLs in the "下载链接.text" file in the same directory and check their validity
concurrently; keep valid links (returning 2xx/3xx or supporting Range fetch of the first byte)
in "下载链接_有效.text", write invalid or inaccessible links to "下载链接_无效.text",
and record the process and statistics into "过滤空链接.log".
"""  # Top-level description: details the script goal and output files

import os  # Path and file handling
import sys  # Read Python version info and exit
import time  # Time tracking
from datetime import datetime  # Log timestamps
from concurrent.futures import ThreadPoolExecutor, as_completed  # Concurrent thread pool
from typing import Tuple  # Type annotations
import urllib.request  # Standard library HTTP requests
import urllib.error  # Standard library HTTP error types

# Compute the script's directory (input/output files are all in the same directory)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # absolute path

# Input and output file paths (all .text so downloaders can read them directly)
INPUT_FILE = os.path.join(SCRIPT_DIR, "下载链接.text")  # original link list file
VALID_FILE = os.path.join(SCRIPT_DIR, "下载链接_有效.text")  # filtered valid link file
INVALID_FILE = os.path.join(SCRIPT_DIR, "下载链接_无效.text")  # invalid link record file
LOG_FILE = os.path.join(SCRIPT_DIR, "过滤空链接.log")  # run log file

# Number of concurrent threads (network I/O intensive; increase for speed; adjust to network conditions)
MAX_WORKERS = 64  # default 64 threads
TIMEOUT = 10  # per-request timeout (seconds) to avoid slow blocking

# Common HTTP headers (mimic a common browser for compatibility)
COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36",  # standard browser UA
    "Accept": "*/*",  # accept any content type
    "Connection": "close",  # close the connection immediately after the request to reduce keep-alive usage
}


def log(msg: str) -> None:
    """Simple logging: print and write to the log file (append)"""  # function description
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # current timestamp
    line = f"[{ts}] {msg}"  # assemble log line
    print(line)  # output to terminal
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as lf:  # append to log file
            lf.write(line + "\n")  # write with newline
    except Exception:
        pass  # log write failure does not block the main flow


def head_request(url: str) -> Tuple[int, dict]:
    """Execute a HEAD request; return (status code, response headers); raise on error for the caller to handle"""  # function description
    req = urllib.request.Request(url, method="HEAD", headers=COMMON_HEADERS)  # build HEAD request
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # send request and wait for response
        status = getattr(resp, "status", 200)  # status code read compatible with different Python versions
        headers = dict(resp.headers)  # convert to dict for access
        return status, headers  # return status and headers


def range_get_request(url: str) -> Tuple[int, int]:
    """Execute a GET request with Range: bytes=0-0; return (status code, bytes read)"""  # function description
    req = urllib.request.Request(url, method="GET", headers=COMMON_HEADERS)  # build GET request
    req.add_header("Range", "bytes=0-0")  # request only the first byte to avoid downloading the whole file
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # send request
        status = getattr(resp, "status", 200)  # get status code
        # Read at most 1 byte to verify readability (if the server does not support Range it may return 200 with full content, but we do not continue reading)
        try:
            chunk = resp.read(1)  # read 1 byte
            read_len = len(chunk)  # actual bytes read
        except Exception:
            read_len = 0  # treat read failure as 0
        return status, read_len  # return status and bytes read


def is_valid_status(code: int) -> bool:
    """Determine whether a status code is considered valid (<400 means accessible)"""  # function description
    return 200 <= code < 400  # 2xx/3xx considered valid


def check_url(url: str) -> Tuple[str, bool, int, str]:
    """
    Check whether a single URL is valid:
    1) Prefer HEAD (fast, no body)
    2) If the server does not support HEAD / returns 4xx/5xx, fall back to GET+Range (first byte only)
    Returns (url, is_valid, status code, error description)
    """  # function description
    try:
        status, headers = head_request(url)  # try HEAD
        if is_valid_status(status):  # if the status code is valid
            # If Content-Length exists and is 0, treat as no content (rare)
            cl = int(headers.get("Content-Length", "1") or "1")  # default 1 to conservatively treat as valid
            if cl == 0:  # content length 0
                return url, False, status, "Content-Length=0"  # treat as invalid
            return url, True, status, ""  # valid
        # If HEAD returns an error, try GET+Range as fallback
        status2, read_len = range_get_request(url)  # fallback method
        if is_valid_status(status2) and read_len > 0:  # at least 1 byte read means it exists
            return url, True, status2, ""  # valid
        return url, False, status2, "HEAD/Range check failed"  # invalid
    except urllib.error.HTTPError as e:  # server returned an HTTP error
        code = getattr(e, "code", 0)  # extract error code
        # Some servers do not support HEAD (405/501); fall back to GET+Range
        if code in (405, 501):
            try:
                status2, read_len = range_get_request(url)  # fallback
                if is_valid_status(status2) and read_len > 0:  # verify read
                    return url, True, status2, ""  # valid
                return url, False, status2, "Range fallback check failed"  # invalid
            except Exception as ex:  # fallback also failed
                return url, False, code, f"Range fallback exception: {ex}"  # return exception info
        return url, False, code, f"HTTPError: {e}"  # other HTTP errors
    except urllib.error.URLError as e:  # network-level errors (DNS, connection timeout, etc.)
        return url, False, 0, f"URLError: {e}"  # return error description
    except Exception as e:  # other unknown errors
        return url, False, 0, f"Exception: {e}"  # return error description


def main() -> None:
    """Main flow: read, concurrent check, output results and statistics"""  # function description
    start = time.time()  # record start time
    log("Start filtering empty links")  # start message
    log(f"Python version: {sys.version.split()[0]}")  # output Python version
    log(f"Input file: {INPUT_FILE}")  # input file path
    log(f"Valid output: {VALID_FILE}")  # valid link output path
    log(f"Invalid output: {INVALID_FILE}")  # invalid link output path
    log(f"Log file: {LOG_FILE}")  # log file path
    log(f"Concurrent threads: {MAX_WORKERS}, timeout: {TIMEOUT}s")  # concurrency and timeout params

    if not os.path.exists(INPUT_FILE):  # check whether the input file exists
        log("Input link file does not exist; task terminated")  # termination message
        return  # end program

    # Read all links (strip empty lines and surrounding whitespace)
    with open(INPUT_FILE, "r", encoding="utf-8", errors="ignore") as f:  # open input file
        urls = [line.strip() for line in f if line.strip()]  # build non-empty link list

    total = len(urls)  # total number of links
    if total == 0:  # if empty
        log("Input file has no valid links; task terminated")  # message
        return  # end

    # Initialize statistics counters
    valid_count = 0  # valid count
    invalid_count = 0  # invalid count
    processed = 0  # processed count

    # Create/truncate output files
    open(VALID_FILE, "w", encoding="utf-8").close()  # truncate valid file
    open(INVALID_FILE, "w", encoding="utf-8").close()  # truncate invalid file

    # Start the thread pool for concurrent checks
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:  # create thread pool
        future_to_url = {executor.submit(check_url, url): url for url in urls}  # submit tasks
        # Collect results one by one (in completion order)
        for future in as_completed(future_to_url):  # wait for tasks
            url, ok, status, err = future.result()  # get result tuple
            processed += 1  # increment processed count
            if ok:  # if valid
                valid_count += 1  # increment valid count
                with open(VALID_FILE, "a", encoding="utf-8") as vf:  # append valid links
                    vf.write(url + "\n")  # write link
            else:  # if invalid
                invalid_count += 1  # increment invalid count
                with open(INVALID_FILE, "a", encoding="utf-8") as inf:  # append invalid links
                    inf.write(f"{url}\tstatus={status}\t{err}\n")  # write detailed info

            # Report progress every 1000 processed (avoid being too frequent)
            if processed % 1000 == 0 or processed == total:  # progress condition
                log(f"Progress: {processed}/{total} | Valid: {valid_count} | Invalid: {invalid_count}")  # print progress

    # Final statistics and elapsed time
    elapsed = time.time() - start  # compute elapsed seconds
    log(f"Done: {total} total | {valid_count} valid | {invalid_count} invalid | {elapsed:.1f}s elapsed")  # completion info
    log(f"Valid links output: {VALID_FILE}")  # valid file path
    log(f"Invalid links output: {INVALID_FILE}")  # invalid file path


if __name__ == "__main__":  # standard entry point
    main()  # call main flow

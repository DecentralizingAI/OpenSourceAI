import shlex
import subprocess
from typing import Union

import bittensor as bt
import time

import compute

from collections import deque


queue = deque()

def hashcat_verify(_hash, output) -> Union[str, None]:
    for item in output.split("\n"):
        if _hash in item:
            return item.strip().split(":")[-1]
    return None


# @fifo
def run_hashcat(
    run_id: str,
    _hash: str,
    salt: str,
    mode: str,
    chars: str,
    mask: str,
    timeout: int = compute.pow_timeout,
    hashcat_path: str = compute.miner_hashcat_location,
    hashcat_workload_profile: str = compute.miner_hashcat_workload_profile,
    hashcat_extended_options: str = "",
    initial_start_time=None,
    execution_time=None,
):
    if initial_start_time:
        start_time = initial_start_time
        real_timeout = timeout - (time.time() - initial_start_time)
    else:
        start_time = time.time()
        real_timeout = timeout - (time.time() - start_time)

    if queue and queue[0] != run_id:
        time.sleep(1)
        execution_time = time.time() - start_time
        return run_hashcat(
            run_id=run_id,
            _hash=_hash,
            salt=salt,
            mode=mode,
            chars=chars,
            mask=mask,
            hashcat_path=hashcat_path,
            hashcat_workload_profile=hashcat_workload_profile,
            hashcat_extended_options=hashcat_extended_options,
            initial_start_time=start_time,
            execution_time=execution_time,
        )
    else:
        bt.logging.info(f"{run_id}: ♻️  Challenge processing")

    unknown_error_message = f"{run_id}: ❌ run_hashcat execution failed"
    try:
        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        RUNPOD STUB IS LEFT UNIMPLMENTED. THIS IS SIMPLY A DEMONSTRATION OF THE EXPLOIT.
        run_pod returns dataclass[return_code: int, output: str]
        Output is the cracked hash.
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """
        result = run_pod(hashcat_path, _hash, salt, mode, str(chars), mask)
        """
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        if execution_time and execution_time >= timeout:
            raise subprocess.TimeoutExpired("Serverless run ran too long", timeout)

        execution_time = time.time() - start_time

        # If hashcat returns a valid result
        if result.returncode == 0:
            if result.output:
                bt.logging.success(
                    f"{run_id}: ✅ Challenge {result} found in {execution_time:0.2f} seconds !"
                )
                queue.popleft()
                return {
                    "password": result.output,
                    "local_execution_time": execution_time,
                    "error": None,
                }
        else:
            error_message = f"{run_id}: ❌ Hashcat execution failed with code {result.returncode}"
            bt.logging.warning(error_message)
            queue.popleft()
            return {
                "password": None,
                "local_execution_time": execution_time,
                "error": error_message,
            }

    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        error_message = f"{run_id}: ❌ Hashcat execution timed out"
        bt.logging.warning(error_message)
        queue.popleft()
        return {
            "password": None,
            "local_execution_time": execution_time,
            "error": error_message,
        }
    except Exception as e:
        execution_time = time.time() - start_time
        bt.logging.warning(f"{unknown_error_message}: {e}")
        queue.popleft()
        return {
            "password": None,
            "local_execution_time": execution_time,
            "error": f"{unknown_error_message}: {e}",
        }
    bt.logging.warning(f"{unknown_error_message}: no exceptions")
    queue.popleft()
    return {
        "password": None,
        "local_execution_time": execution_time,
        "error": f"{unknown_error_message}: no exceptions",
    }


def run_miner_pow(
    run_id: str,
    _hash: str,
    salt: str,
    mode: str,
    chars: str,
    mask: str,
    hashcat_path: str = compute.miner_hashcat_location,
    hashcat_workload_profile: str = compute.miner_hashcat_workload_profile,
    hashcat_extended_options: str = "",
):
    if len(queue) <= 0:
        bt.logging.info(f"{run_id}: 💻 Challenge received")
    else:
        bt.logging.info(f"{run_id}: ⏳ An instance running - added in the queue.")

    # Add to the queue the challenge id
    queue.append(run_id)

    result = run_hashcat(
        run_id=run_id,
        _hash=_hash,
        salt=salt,
        mode=mode,
        chars=chars,
        mask=mask,
        hashcat_path=hashcat_path,
        hashcat_workload_profile=hashcat_workload_profile,
        hashcat_extended_options=hashcat_extended_options,
    )
    return result

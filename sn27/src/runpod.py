import runpod
import subprocess
import typing as T
import shlex

def hashcat_verify(_hash: str, output: str) -> T.Union[str, None]:
    for item in output.split("\n"):
        if _hash in item:
            return item.strip().split(":")[-1]
    return None

def solve_hash(hash: str, salt: str, hashcat_path: str, mode: int, chars: str, mask: str) -> T.Optional[str]:
    command = [
                hashcat_path,
                f"{hash}:{salt}",
                "-a",
                "3",
                "-D",
                "2",
                "-m",
                mode,
                "-1",
                str(chars),
                mask,
                "-w",
                3,
                "",
            ]
    command_str = " ".join(shlex.quote(arg) for arg in command)

    process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return hashcat_verify(hash, process.stdout)

runpod.serverless.start({"handler": solve_hash})

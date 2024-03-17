# Basis Potential SN27 Exploits & Issues

## Disclaimer

The contents of this report are provided for open source contributors to fix. This contents of this report should NOT be used in any malicious way.

## Introduction

### Intention

SN27 is a bittensor subnet dedicated to providing compute to the network.

Compute is intended to be vended through bare-metal style docker containers that a compute requester can ssh into, similar to an Amazon EC2.

### Validation Mechanism

SN27 miners are validated by a POW and hardware spec mechanism. An important note is that this is entirely seperate from their intended function of an ssh-able docker container.

#### POW

Miners are requested by validators to calculate a hash on a byte array of length n. The length of the byte string and time of the solve contributes to the miner's score.

#### Hardware Specs

Validators are able to query the hardware specs of the miner via a python script which is obfuscated and ran through as an executable.

This hardware spec does not directly contribute to the Miner's score - rather it is used for reporting & analysis purposes by the validators when vending theoretical compute workloads. This disconnect is further interesting in and of itself.

The hardware spec executable also provides a util function that returns if docker is installed on the miner or not. This _does_ have a direct impact on the miner's score - halfing it if not present.

## Exploits

### POW

#### Manifestation

One potential POW exploit takes advantage of serverless GPU compute. A given validator will request a miner solve a compute task every 10 to 16 minutes. Since there are 64 validators, we can expect a new hash challenge [every 10 to 15 seconds](https://github.com/neuralinternet/compute-subnet/blame/main/neurons/validator.py#L610). The timeout for a hash request is defaulted to [30 seconds](https://github.com/neuralinternet/compute-subnet/blob/85de1b2717212caa02a8a8914a44327c5f529dd7/compute/__init__.py#L37).

#### Takeaway

Given this, one could theoretically use serverless GPU compute to crack the hash of high difficulty hashes very quickly, while holding no actual compute power themselves. Since the subnet has no basis to assess compute power outside of the hash cracking, the miner would be rewarded very highly for potentially very little cost.

#### Implementation

An example of how to take advantage of this exploit could be found below.

1. The miner uses hashcat to crack the hash.
2. The serverless GPU platform RunPod could be used to run hashcat in a serverless docker container, such as demonstrated below:

_RunPod Docker Code_

```python
import runpod

def hashcat_verify(_hash, output) -> Union[str, None]:
    for item in output.split("\n"):
        if _hash in item:
            return item.strip().split(":")[-1]
    return None

def solve_hash(hash: str, salt: str, hashcat_path: str, mode: int, chars: str, mask: str) -> Optional[str]:
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
        timeout=real_timeout,
    )
    return hashcat_verify(process.stdout)

runpod.serverless.start({"handler": solve_hash})
```

_Miner Modification_

See pow.py

### Hardware Specs

#### Manifestation

Hardware specs are analyzed in SN27 using a python script encoded as a binary executable. You can reference the script [here](https://github.com/neuralinternet/compute-subnet/blob/main/neurons/Validator/script.py).

The script is turned into a bin using [Pyinstaller](https://pyinstaller.org/en/stable/).

The script contains a "secret key" which is used to encrypt the output of the utility functions within. The encryption of this executable is meant to make it impossible for miners to fake their response to the output of this executable. The output of the executable is "signed" with the secret key on [line 26](https://github.com/neuralinternet/compute-subnet/blob/main/neurons/Validator/script.py#L26). The key is randomized by the validator and injected into the script at miner request time [here](https://github.com/neuralinternet/compute-subnet/blob/85de1b2717212caa02a8a8914a44327c5f529dd7/neurons/Validator/app_generator.py#L49C58-L49C68). This randomization is obviously critical, as a miner who knows the secret key could fake their specification output.

To reiterate: the assumption of the validator is that the miner has no way to identify the secret key. If the miner does aquire the secret key, it can return any arbitrary information to the validator and the validator will trust the response completely.

#### Takeaway

The "secret key" is obviously not entirely secret. A malicious miner could inspect the executable memory space to identify the secret key, and return false information to the validator. This renders the integrity of the entire SN27 highly questionable.

## Issues

### POW

Given the miners are assessed on their ability to solve hashes, and this POW is intended to use all of the compute available on the machine, miners cannot be assessed & rewarded while they are serving docker containers to end-users. This renders the actual usefulness of the subnet into question - the mechanism for incentivization must be more closely tied to the actual intended function of the subnet.

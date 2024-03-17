# Miner Orchestration Framework

This repository enables users to autonomously run and manage a fleet of miners.

The framework comes with in-built monitoring of dead miners and price movements, 
Bittensor subnet miners cost a variable amount of tao to register, based on supply-demand mechanics.

## Features

- Register a fleet of miners that run on the same machine on separate tmux processes
- Only register miners at low registration prices to avoid paying high costs
- Detect dead miners (deregistered after immunity period), and replace them with a new miner
- Manages hotkeys on-device
- Update existing miners with new models while minimizing miner down-time costs

## Run

```
python3 orchestration.py
 --wallet {cold wallet name}
 --model {model name}
 --max-cost {in tao}
 --restart {bool: restart all existing miners with new parameters}
```


## Requirements

- Bittensor CLI
- Dependencies to run miner
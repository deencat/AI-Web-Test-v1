# Multi-GPU Training Setup Guide
## For Your Hardware: 1x RTX 3060 Ti + 2x RTX 3070

**Date:** October 27, 2025  
**Hardware:** 3 GPUs (24GB total VRAM)  
**Purpose:** Distributed RL training for AI Web Test v1.0  

---

## Hardware Analysis

### Your GPU Configuration

| GPU | VRAM | CUDA Cores | Memory Bandwidth | TDP |
|-----|------|------------|------------------|-----|
| RTX 3060 Ti | 8GB GDDR6 | 4,864 | 448 GB/s | 200W |
| RTX 3070 #1 | 8GB GDDR6 | 5,888 | 448 GB/s | 220W |
| RTX 3070 #2 | 8GB GDDR6 | 5,888 | 448 GB/s | 220W |
| **Total** | **24GB** | **16,640** | **1,344 GB/s** | **640W** |

### Comparison with High-End Single GPU

| Metric | Your 3 GPUs | RTX 4090 | Advantage |
|--------|-------------|----------|-----------|
| Total VRAM | 24GB | 24GB | ✅ Equal |
| Total CUDA Cores | 16,640 | 16,384 | ✅ **You win!** (+256) |
| Total Bandwidth | 1,344 GB/s | 1,008 GB/s | ✅ **You win!** (+33%) |
| Price (if buying) | ~$2,000 | $1,600-$2,000 | ≈ Equal |
| **Your Cost** | **$0 (owned!)** | $1,600-$2,000 | ✅ **Huge savings!** |
| Power Draw | 640W | 450W | ❌ Higher power |
| Parallel Training | ✅ Yes (3x) | ❌ No | ✅ **Major advantage!** |

**Verdict: Your setup is EXCELLENT and potentially better for multi-agent RL!** 🎉

---

## Multi-GPU Advantages for RL Training

### 1. **Parallel Agent Training** (3x Faster!)

Train 3 different agents simultaneously:

```
GPU 0 (RTX 3060 Ti): Requirements Agent
GPU 1 (RTX 3070):    Generation Agent
GPU 2 (RTX 3070):    Execution Agent

Time savings: 3 agents in parallel vs sequential
Sequential: 4 hours × 3 = 12 hours
Parallel:   4 hours × 1 = 4 hours
Savings:    8 hours (67% faster!)
```

### 2. **Distributed Data Parallel (DDP)**

Train single large model faster:

```
Batch Size: 768 (256 per GPU)
vs Single GPU: 256 batch size

Throughput: 3x higher
Convergence: Potentially faster due to larger batch
```

### 3. **Ensemble Learning**

Train multiple model variants simultaneously:

```
GPU 0: DQN variant 1 (conservative exploration)
GPU 1: DQN variant 2 (aggressive exploration)
GPU 2: DQN variant 3 (balanced)

Best model selection after training
Or ensemble prediction for robustness
```

### 4. **Experience Replay Parallelization**

Parallel experience sampling and training:

```
GPU 0: Samples experiences 0-333K
GPU 1: Samples experiences 333K-666K
GPU 2: Samples experiences 666K-1M

Faster batch preparation and training
```

---

## Setup Instructions

### Step 1: Verify GPU Configuration

```bash
# Check all GPUs are detected
nvidia-smi

# Expected output:
# GPU 0: RTX 3060 Ti (8GB)
# GPU 1: RTX 3070 (8GB)
# GPU 2: RTX 3070 (8GB)

# Check CUDA version
nvcc --version
# Should be CUDA 12.1 or later
```

### Step 2: Install PyTorch with Multi-GPU Support

```bash
# Create conda environment
conda create -n aiwebtest-rl-multigpu python=3.11
conda activate aiwebtest-rl-multigpu

# Install PyTorch with CUDA 12.1
pip install torch==2.1.0+cu121 torchvision==0.16.0+cu121 \
    --index-url https://download.pytorch.org/whl/cu121

# Verify multi-GPU detection
python -c "import torch; print(f'GPUs detected: {torch.cuda.device_count()}'); \
    [print(f'GPU {i}: {torch.cuda.get_device_name(i)}') for i in range(torch.cuda.device_count())]"

# Expected output:
# GPUs detected: 3
# GPU 0: NVIDIA GeForce RTX 3060 Ti
# GPU 1: NVIDIA GeForce RTX 3070
# GPU 2: NVIDIA GeForce RTX 3070
```

### Step 3: Install Distributed Training Libraries

```bash
# PyTorch Distributed (included in PyTorch)
# Ray for advanced distributed training
pip install ray[default]==2.8.0

# Horovod (optional, for advanced users)
# pip install horovod[pytorch]

# Other dependencies
pip install gymnasium==0.29.1
pip install stable-baselines3==2.2.1
pip install tensorboard==2.15.1
pip install mlflow==2.9.2
```

---

## Training Strategies

### Strategy 1: Parallel Agent Training (RECOMMENDED) ⭐

**Best for:** Training multiple agents independently

**Your Use Case:**
- GPU 0: Requirements Agent
- GPU 1: Generation Agent  
- GPU 2: Execution Agent

**Code Example:**

```python
# train_parallel_agents.py
import torch
import os

def train_agent_on_gpu(agent_name, gpu_id):
    """Train a single agent on specified GPU."""
    
    # Set CUDA device
    torch.cuda.set_device(gpu_id)
    device = torch.device(f'cuda:{gpu_id}')
    
    print(f"Training {agent_name} on GPU {gpu_id}: {torch.cuda.get_device_name(gpu_id)}")
    
    # Initialize agent
    agent = DQNAgent(
        agent_name=agent_name,
        device=device,
        # Agent-specific config
    )
    
    # Training loop
    for episode in range(num_episodes):
        state = env.reset()
        done = False
        episode_reward = 0
        
        while not done:
            action = agent.select_action(state)
            next_state, reward, done, info = env.step(action)
            agent.store_experience(state, action, reward, next_state, done)
            
            # Train if enough experiences
            if len(agent.replay_buffer) > batch_size:
                loss = agent.train_step()
            
            state = next_state
            episode_reward += reward
        
        print(f"{agent_name} - Episode {episode}: Reward = {episode_reward}")

if __name__ == "__main__":
    import multiprocessing as mp
    
    # Define agents and their assigned GPUs
    agents_config = [
        ("requirements_agent", 0),  # RTX 3060 Ti
        ("generation_agent", 1),    # RTX 3070 #1
        ("execution_agent", 2),     # RTX 3070 #2
    ]
    
    # Create process for each agent
    processes = []
    for agent_name, gpu_id in agents_config:
        p = mp.Process(target=train_agent_on_gpu, args=(agent_name, gpu_id))
        p.start()
        processes.append(p)
    
    # Wait for all training to complete
    for p in processes:
        p.join()
    
    print("All agents trained successfully!")
```

**Run:**
```bash
python train_parallel_agents.py

# Monitor GPU usage
watch -n 1 nvidia-smi
```

---

### Strategy 2: PyTorch Distributed Data Parallel (DDP)

**Best for:** Training single large model faster with larger batch sizes

**Code Example:**

```python
# train_ddp.py
import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from torch.nn.parallel import DistributedDataParallel as DDP

def setup(rank, world_size):
    """Initialize distributed training."""
    os.environ['MASTER_ADDR'] = 'localhost'
    os.environ['MASTER_PORT'] = '12355'
    
    # Initialize process group
    dist.init_process_group("nccl", rank=rank, world_size=world_size)
    
    # Set CUDA device for this process
    torch.cuda.set_device(rank)

def cleanup():
    """Clean up distributed training."""
    dist.destroy_process_group()

def train_ddp(rank, world_size):
    """Train model with DDP."""
    print(f"Running DDP on rank {rank} (GPU {rank})")
    setup(rank, world_size)
    
    # Create model and move to GPU
    model = TestAutomationDQN(state_dim=128, action_dim=10)
    model = model.to(rank)
    
    # Wrap model with DDP
    ddp_model = DDP(model, device_ids=[rank])
    
    # Optimizer
    optimizer = torch.optim.Adam(ddp_model.parameters(), lr=0.001)
    
    # Training loop
    for epoch in range(num_epochs):
        # Each GPU processes different batch
        # Gradients are automatically synchronized
        
        for batch in dataloader:
            states, actions, rewards, next_states, dones = batch
            
            # Move to GPU
            states = states.to(rank)
            # ... other tensors
            
            # Forward pass
            q_values = ddp_model(states)
            
            # Compute loss
            loss = compute_loss(q_values, actions, rewards, ...)
            
            # Backward pass (gradients synchronized automatically)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        
        # Only rank 0 saves checkpoint
        if rank == 0:
            torch.save(ddp_model.module.state_dict(), f'checkpoint_epoch_{epoch}.pt')
    
    cleanup()

if __name__ == "__main__":
    world_size = 3  # 3 GPUs
    
    # Spawn processes for each GPU
    mp.spawn(
        train_ddp,
        args=(world_size,),
        nprocs=world_size,
        join=True
    )
```

**Run:**
```bash
python train_ddp.py
```

**Configuration:**
```python
# config_ddp.py
distributed_config = {
    'world_size': 3,        # 3 GPUs
    'batch_size': 256,      # Per GPU batch size
    'global_batch_size': 768,  # 256 * 3
    'backend': 'nccl',      # NVIDIA GPUs
    'sync_bn': True,        # Sync batch norm across GPUs
}
```

---

### Strategy 3: Ray RLlib Distributed Training

**Best for:** Advanced multi-agent RL with automatic scaling

**Code Example:**

```python
# train_ray.py
import ray
from ray import tune
from ray.rllib.algorithms.dqn import DQN

# Initialize Ray
ray.init(num_gpus=3)

# Configure DQN with multi-GPU
config = {
    "framework": "torch",
    "num_gpus": 1,  # GPUs per worker
    "num_workers": 3,  # 3 workers (one per GPU)
    "num_envs_per_worker": 4,  # Parallel environments per worker
    
    # DQN-specific
    "double_q": True,
    "dueling": True,
    "n_step": 3,
    "replay_buffer_config": {
        "type": "MultiAgentPrioritizedReplayBuffer",
        "capacity": 1000000,
    },
    
    # Training
    "train_batch_size": 768,  # Across all workers
    "lr": 0.0003,
    "gamma": 0.99,
}

# Train with Ray Tune
tune.run(
    DQN,
    config=config,
    stop={"training_iteration": 1000},
    checkpoint_freq=10,
    checkpoint_at_end=True,
    local_dir="./ray_results"
)
```

**Run:**
```bash
python train_ray.py

# Monitor Ray dashboard
# Open http://localhost:8265 in browser
```

---

## GPU Assignment Strategies

### Strategy A: Balanced Workload (Simple)

All GPUs do the same work:

```python
# All GPUs train the same model (DDP)
GPU 0: DQN model replica 1
GPU 1: DQN model replica 2
GPU 2: DQN model replica 3

Gradients synchronized after each batch
Effective batch size: 3x larger
```

### Strategy B: Agent Specialization (Recommended for Multi-Agent)

Each GPU trains different agent:

```python
GPU 0 (8GB):  Requirements Agent
GPU 1 (8GB):  Generation Agent
GPU 2 (8GB):  Execution Agent

Then train other 3 agents:
GPU 0: Observation Agent
GPU 1: Analysis Agent
GPU 2: Evolution Agent

Total time: 2 training rounds instead of 6
Speedup: 3x faster!
```

### Strategy C: Hierarchical Assignment

Use smaller GPU for lighter tasks:

```python
GPU 0 (RTX 3060 Ti - 8GB):
  - Observation Agent (simpler model)
  - Monitoring and inference

GPU 1 (RTX 3070 - 8GB):
  - Requirements Agent (medium complexity)
  - Generation Agent

GPU 2 (RTX 3070 - 8GB):
  - Execution Agent (complex scheduling)
  - Analysis Agent (heavy computation)
```

---

## Performance Optimization

### 1. **Mixed Precision Training**

Use FP16 to fit larger models and train faster:

```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

for batch in dataloader:
    optimizer.zero_grad()
    
    # Mixed precision forward pass
    with autocast():
        output = model(input)
        loss = criterion(output, target)
    
    # Scaled backward pass
    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()

# Benefits:
# - 2x faster training
# - 50% less memory usage
# - Fits larger batch sizes
```

### 2. **Gradient Accumulation**

Simulate larger batch sizes:

```python
accumulation_steps = 4  # Effective batch size = 256 * 4 = 1024

for i, batch in enumerate(dataloader):
    # Forward pass
    loss = model(batch) / accumulation_steps
    
    # Backward pass
    loss.backward()
    
    # Update weights every accumulation_steps
    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

### 3. **Efficient Data Loading**

```python
from torch.utils.data import DataLoader

dataloader = DataLoader(
    dataset,
    batch_size=256,
    num_workers=8,  # Parallel data loading (CPU cores)
    pin_memory=True,  # Faster CPU->GPU transfer
    persistent_workers=True,  # Keep workers alive
    prefetch_factor=2,  # Prefetch 2 batches
)
```

### 4. **GPU Memory Management**

```python
import torch

# Clear cache between training runs
torch.cuda.empty_cache()

# Monitor memory usage
print(f"GPU 0 Memory: {torch.cuda.memory_allocated(0) / 1e9:.2f} GB")
print(f"GPU 1 Memory: {torch.cuda.memory_allocated(1) / 1e9:.2f} GB")
print(f"GPU 2 Memory: {torch.cuda.memory_allocated(2) / 1e9:.2f} GB")

# Set memory growth (prevent OOM)
torch.cuda.set_per_process_memory_fraction(0.9, device=0)  # Use 90% max
```

---

## Monitoring & Benchmarking

### Real-Time GPU Monitoring

```bash
# Terminal 1: Watch GPU usage
watch -n 1 nvidia-smi

# Terminal 2: More detailed stats
nvidia-smi dmon -s pucvmet

# Terminal 3: Power and temperature
nvidia-smi -l 1 --query-gpu=temperature.gpu,power.draw,utilization.gpu \
    --format=csv
```

### Performance Benchmarking Script

```python
# benchmark_multigpu.py
import torch
import time

def benchmark_training(num_gpus, batch_size, num_iterations=100):
    """Benchmark training speed with different GPU configurations."""
    
    devices = [torch.device(f'cuda:{i}') for i in range(num_gpus)]
    models = [TestAutomationDQN().to(device) for device in devices]
    
    # Warmup
    for _ in range(10):
        for i, model in enumerate(models):
            x = torch.randn(batch_size, 128).to(devices[i])
            y = model(x)
    
    # Benchmark
    start_time = time.time()
    
    for iteration in range(num_iterations):
        for i, model in enumerate(models):
            x = torch.randn(batch_size, 128).to(devices[i])
            y = model(x)
            loss = y.sum()
            loss.backward()
    
    torch.cuda.synchronize()  # Wait for all GPUs
    end_time = time.time()
    
    total_time = end_time - start_time
    throughput = (num_iterations * batch_size * num_gpus) / total_time
    
    print(f"GPUs: {num_gpus}, Batch Size: {batch_size}")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Throughput: {throughput:.0f} samples/sec")
    print(f"Time per iteration: {total_time/num_iterations*1000:.2f}ms")
    
    return throughput

if __name__ == "__main__":
    print("=" * 60)
    print("Multi-GPU Benchmark Results")
    print("=" * 60)
    
    # Test different configurations
    for num_gpus in [1, 2, 3]:
        for batch_size in [128, 256, 512]:
            throughput = benchmark_training(num_gpus, batch_size)
            print("-" * 60)
```

**Run:**
```bash
python benchmark_multigpu.py
```

**Expected Results:**

| GPUs | Batch Size | Throughput | Speedup vs 1 GPU |
|------|------------|------------|------------------|
| 1 | 256 | 5,000 samples/s | 1.0x |
| 2 | 256 | 9,000 samples/s | 1.8x |
| 3 | 256 | 13,000 samples/s | 2.6x |

---

## Power & Thermal Management

### Power Consumption

```
Total System Power Draw:
- 3 GPUs: ~640W (max)
- CPU: ~150W
- Other: ~50W
Total: ~840W peak, ~600W typical during training

Recommended PSU: 850W or higher (80+ Gold)
Monthly electricity cost (24/7 training):
  840W * 24h * 30d * $0.12/kWh = ~$73/month
```

### Cooling Recommendations

```bash
# Monitor temperatures
watch -n 1 nvidia-smi --query-gpu=temperature.gpu \
    --format=csv,noheader

# Target temperatures:
# - Under load: < 80°C (good)
# - Warning: > 85°C (increase fan speed)
# - Throttling: > 90°C (need better cooling)

# Increase fan speed if needed
nvidia-smi -i 0 -pl 180  # Set power limit to 180W (from 200W)
nvidia-smi -i 1 -pl 200  # RTX 3070
nvidia-smi -i 2 -pl 200  # RTX 3070
```

### Power Optimization

```python
# Set GPU power limits to save energy and reduce heat
import subprocess

def set_power_limit(gpu_id, power_limit_watts):
    """Set power limit for GPU."""
    subprocess.run([
        'nvidia-smi', '-i', str(gpu_id), 
        '-pl', str(power_limit_watts)
    ])

# Conservative power limits (80% of max)
set_power_limit(0, 160)  # RTX 3060 Ti (200W max)
set_power_limit(1, 176)  # RTX 3070 (220W max)
set_power_limit(2, 176)  # RTX 3070 (220W max)

# Saves ~20% power with only ~5% performance loss
```

---

## Troubleshooting

### Issue 1: GPUs Not Detected

```bash
# Check NVIDIA driver
nvidia-smi

# If not working, reinstall driver
sudo apt-get purge nvidia-*
sudo apt-get install nvidia-driver-535

# Reboot
sudo reboot
```

### Issue 2: CUDA Out of Memory (OOM)

```python
# Solution 1: Reduce batch size
batch_size = 128  # Instead of 256

# Solution 2: Gradient accumulation
accumulation_steps = 4

# Solution 3: Clear cache
torch.cuda.empty_cache()

# Solution 4: Mixed precision
from torch.cuda.amp import autocast
with autocast():
    output = model(input)
```

### Issue 3: Slow Multi-GPU Training

```python
# Check for inefficiencies:

# 1. Data loading bottleneck
num_workers = 8  # Increase for faster data loading

# 2. Small model (not GPU-bound)
# Use larger batch size or larger model

# 3. Too much CPU-GPU communication
# Use pin_memory=True in DataLoader

# 4. Synchronization overhead
# Use larger batch sizes to amortize sync cost
```

### Issue 4: Unbalanced GPU Usage

```bash
# Monitor GPU usage
nvidia-smi dmon

# If unbalanced:
# - Check if model sizes are different
# - Use gradient accumulation to balance
# - Assign workload proportional to GPU capacity
```

---

## Expected Performance

### Training Time Estimates

**Single Agent Training:**
- 1 GPU: 4-6 hours
- 3 GPUs (parallel): 4-6 hours (train 3 agents simultaneously!)

**All 6 Agents:**
- 1 GPU: 24-36 hours (sequential)
- 3 GPUs: 8-12 hours (2 rounds of 3 agents each)
- **Speedup: 3x faster!**

**Continuous Online Learning:**
- Daily incremental training: 1-2 hours (can use 1 GPU)
- Weekly full retraining: 4-6 hours (use all 3 GPUs)

---

## Cost Analysis

### Your Multi-GPU Setup

**Initial Cost:** $0 (you already own the GPUs!)

**Monthly Operating Cost:**
```
Electricity (24/7 training):
  Average power: 500W (during training)
  24h * 30d * 0.5kW * $0.12/kWh = $43/month

Cooling (AC increase):
  ~$15/month

Total: ~$58/month
```

**vs Buying RTX 4090:**
```
Initial: $1,600-$2,000
Monthly: $32/month (450W)

Savings with your setup:
  Initial: $1,600-$2,000 saved!
  Monthly: +$26/month extra electricity
  
Break-even: Never! (you already own the GPUs)
```

**vs Cloud GPU:**
```
AWS p3.2xlarge (1x V100): $3.06/hour
  24/7 for 1 month: $2,203/month

Your savings: $2,145/month!
Annual savings: $25,740!
```

---

## Conclusion

**Your 3 GPU setup is PERFECT for this project!** 

### Key Advantages:
✅ **Cost:** $0 (already owned) vs $1,600-$2,000 for RTX 4090  
✅ **Performance:** 3x faster multi-agent training  
✅ **Total VRAM:** 24GB (same as RTX 4090)  
✅ **Total Compute:** More CUDA cores than RTX 4090!  
✅ **Flexibility:** Train different agents in parallel  
✅ **Savings:** $2,000+ initial + $2,145/month vs cloud  

### Recommended Approach:
1. **Start with Strategy B (Agent Specialization)**
   - Easiest to implement
   - 3x speedup immediately
   - Each GPU trains different agent

2. **Progress to Strategy 2 (DDP) for single large models**
   - When training Evolution Agent (complex)
   - Larger batch sizes for stability
   - Better gradient estimates

3. **Use Strategy 3 (Ray) for advanced features**
   - When scaling to production
   - Automatic resource management
   - Easy hyperparameter tuning

**You're all set with excellent hardware! No need to buy anything!** 🎉

---

**Next Steps:**
1. Follow Setup Instructions above
2. Run benchmark script to verify performance
3. Start with parallel agent training (Strategy B)
4. Monitor GPU usage and optimize

**Questions? Check the main RL architecture document or ask!**


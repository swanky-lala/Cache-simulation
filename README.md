# Cache-Simulator

This Python program provides a cache simulator for analyzing cache performance using various cache configurations. It includes classes for implementing different types of caches and methods for simulating cache behavior based on memory access traces.

Cache Types

1. Write-Through Cache (Part 1 & 2)
Simulates a write-through cache configuration.
Provides statistics on cache hits, misses, hit rates, and average memory access time (AMAT).
Supports varying cache associativity levels.
2. Write-Back Cache (Part 3 & 4)
Implements a write-back cache strategy.
Similar to the write-through cache, it calculates cache performance metrics including hit rates and AMAT.
Allows experimenting with different cache sizes and associativities.
3. Two Cache Levels (Part 5)
Extends the simulation to include two cache levels: L1 and L2 caches.
Provides insights into the performance impact of having multiple cache levels.
Analyzes hit rates and AMAT for both L1 and L2 caches.
4. Part6-Data Collection
Collects data on cache performance by varying parameters such as L1 cache size, block size, and L2 cache size.
Presents graphical visualizations of cache hit rates and AMAT for different configurations.
Usage

Select the cache simulation option based on your choice (1, 2, 3, or 4).
Provide the path to the memory access trace file.
Analyze the cache performance metrics displayed, including hit rates, miss rates, and AMAT.
Experiment with different cache configurations to observe their impact on performance.

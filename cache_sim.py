import os
import matplotlib.pyplot as plt

class CacheBase:
    def __init__(self, total_size_bytes, block_size_bytes, set_associativity, hit_time, miss_penalty, next_cache):
        self.total_size_bytes = total_size_bytes
        self.block_size_bytes = block_size_bytes
        self.set_associativity = set_associativity
        self.hit_time = hit_time
        self.miss_penalty = miss_penalty

        self.num_sets = total_size_bytes // (block_size_bytes * set_associativity)
        self.set_size = set_associativity

        self.cache = [[] for _ in range(self.num_sets)]
        self.valid_bits = [[False] * self.set_size for _ in range(self.num_sets)]
        self.lru_counters = [[0] * self.set_size for _ in range(self.num_sets)]

        # Additional attributes to track cache statistics
        self.access_hits = 0
        self.access_misses = 0
        self.access_total = 0
        self.access_hit_rate = 0  # Added attribute for instruction hit rate

        # Next level cache (L2 and up)
        self.next_cache = next_cache

    # def find_set_and_block_addr(self, address):
    #     set_index = (address // self.block_size_bytes) % self.num_sets
    #     block_index = address // self.block_size_bytes
    #     return set_index, block_index

    def find_set_and_block(self, address):
        set_index = (address // self.block_size_bytes) % self.num_sets
        block_addr = address // self.block_size_bytes
        return set_index, block_addr

    # def calculate_percentage(self, value, total=None):
    #     total = total or value
    #     if total == 0:
    #         return "0.00%"
    #     return f"{(value / total) * 100:.2f}%"

    # def instruction_fetch(self, address):
    #     set_index, block_offset = self.find_set_and_block(address)

    #     if any(block == address for block in self.cache[set_index]):
    #         self.update_lru_counters(set_index, address)
    #         self.instruction_accesses += 1
    #         return f"Cache Hit: Instruction from set {set_index}, block {block_offset}"

    #     self.instruction_misses += 1
    #     return "Cache Miss"


class WriteThroughCache(CacheBase):
    def __init__(self, total_size_bytes, block_size_bytes, set_associativity, hit_time, miss_penalty, next_cache):
        super().__init__(total_size_bytes, block_size_bytes, set_associativity, hit_time, miss_penalty, next_cache)
        # print(f"*******{self.access_hits}, {self.access_misses}")

    def write_to_cache(self, address, write_flag, next_level_cache):
        self.access_total += 1
        self.access_misses += 1
        set_index, block_addr = self.find_set_and_block(address)

        # in case address already in cache, remove from cache
        if block_addr in self.cache[set_index]:
            self.cache[set_index].remove(block_addr)

        # insert to front for most recent reference
        self.cache[set_index].insert(0, block_addr)
        if len(self.cache[set_index]) > self.set_size:
            # pop from tail (least recently used item)
            self.cache[set_index].pop()
            self.access_total += 0

    def read_from_cache(self, address, next_level_cache):
        set_index, block_addr = self.find_set_and_block(address)
        for block in self.cache[set_index]:
            if block == block_addr:
                self.access_hits += 1
                self.access_total += 1
                # Move matched address to front (most recent reference)
                self.cache[set_index].remove(block_addr)
                self.cache[set_index].insert(0, block_addr)
                return
        self.write_to_cache(address, False, None)


class WriteBackCache(CacheBase):
    def __init__(self, total_size_bytes, block_size_bytes, set_associativity, hit_time, miss_penalty, next_cache):
        super().__init__(total_size_bytes, block_size_bytes, set_associativity, hit_time, miss_penalty, next_cache)

    def write_to_cache(self, address, write_flag,
                       next_level_cache):  # write_flag = False when a write is caused by a read miss
        dirty_bit = False
        set_index, block_addr = self.find_set_and_block(address)
        # Only toggle dirty_bits for write access (not write to cache from memory due to a missed read)
        if write_flag == True:
            dirty_bit = True
        # in case address already in cache, remove from cache
        for i in range(len(self.cache[set_index])):
            # address[0] is address, address[1] is dirty bit
            if self.cache[set_index][i][0] == block_addr:
                self.cache[set_index].pop(i)
                break
        # insert to front for most recent reference
        self.cache[set_index].insert(0, [block_addr, dirty_bit])
        if len(self.cache[set_index]) > self.set_size:
            evicted = self.cache[set_index].pop()
            # if evicted address is dirty, it needs to be written to memory, hence count as a miss
            if evicted[1] == True:
                if next_level_cache != None:
                    next_level_cache.write_to_cache(evicted[1] * self.block_size_bytes, write_flag,
                                                    next_level_cache.next_cache)
                else:
                    self.access_total += 1
                    self.access_misses += 1
                    return
        if write_flag == True:
            self.access_total += 1
            self.access_hits += 1
        else:
            self.access_total += 1
            self.access_misses += 1


#**********************************************************************


    #**********************************************************************

    def read_from_cache(self, address, next_level_cache):
        set_index, block_addr = self.find_set_and_block(address)
        for i in range(len(self.cache[set_index])):
            if self.cache[set_index][i][0] == block_addr:
                self.access_hits += 1
                self.access_total += 1
                # Move matched address to front (most recent reference)
                matched_block = self.cache[set_index].pop(i)
                self.cache[set_index].insert(0, matched_block)
                return
        # handle miss by getting address from next level cache
        self._handle_cache_miss(address, next_level_cache=next_level_cache)
        # update current cache
        self.write_to_cache(address, write_flag=False, next_level_cache=None)

    def _handle_cache_miss(self, address, next_level_cache):
        if next_level_cache != None:
            next_level_cache.read_from_cache(address, next_level_cache=next_level_cache.next_cache)


def calculate_percentage(value, total=None):
    total = total or value
    if total == 0:
        return 0
    return (value / total) * 100


def simulate_l1_cache(l1d_cache, l1i_cache, trace_file_path):
    with open(trace_file_path, "r") as file:
        for line in file:
            memory_access_type, address_hex = line.split()
            address = int(address_hex, 16)

            if memory_access_type == '0':
                l1d_cache.read_from_cache(address, next_level_cache=None)
            elif memory_access_type == '1':
                l1d_cache.write_to_cache(address, write_flag=True, next_level_cache=None)
            elif memory_access_type == '2':
                l1i_cache.read_from_cache(address, next_level_cache=None)

        data_hit_rate = calculate_percentage(l1d_cache.access_hits, l1d_cache.access_total)
        data_miss_rate = calculate_percentage(l1d_cache.access_misses, l1d_cache.access_total)
        instruction_hit_rate = calculate_percentage(l1i_cache.access_hits, l1i_cache.access_total)
        instruction_miss_rate = calculate_percentage(l1i_cache.access_misses, l1i_cache.access_total)
        total_miss_rate = calculate_percentage(l1d_cache.access_misses + l1i_cache.access_misses,
                                               l1d_cache.access_total + l1i_cache.access_total)
        amat = l1i_cache.hit_time + (total_miss_rate / 100) * l1i_cache.miss_penalty

        # print(f"L1 Data Hits: {l1d_cache.access_hits} ({data_hit_rate:.2f}) Total: {l1d_cache.access_total}")
        # print(f"L1 Data Misses: {l1d_cache.access_misses} ({data_miss_rate:.2f})")
        # print(
        #     f"L1 Instruction Hits: {l1i_cache.access_hits} ({instruction_hit_rate:.2f}) Total: {l1i_cache.access_total}")
        # print(f"L1 Instruction Misses: {l1i_cache.access_misses} ({instruction_miss_rate:.2f})")
        # print(f"AMAT: {amat:.2f}\n")

        print(f"|{l1i_cache.set_associativity:15}|{l1i_cache.access_total:15}|{l1i_cache.access_misses:15}|{instruction_hit_rate:14.2f}%|{l1d_cache.access_total:15}|{l1d_cache.access_misses:15}|{data_hit_rate:14.2f}%|{amat:15.2f}|")
        print("|" + ('-' * 15 + "|")*8)


def simulate_l1_l2_cache(l1d_cache, l1i_cache, l2_cache, trace_file_path, stats):
    with open(trace_file_path, "r") as file:
        for line in file:
            memory_access_type, address_hex = line.split()
            address = int(address_hex, 16)

            if memory_access_type == '0':
                l1d_cache.read_from_cache(address, next_level_cache=l2_cache)
            elif memory_access_type == '1':
                l1d_cache.write_to_cache(address, write_flag=True, next_level_cache=l2_cache)
            elif memory_access_type == '2':
                l1i_cache.read_from_cache(address, next_level_cache=l2_cache)

        l1d_hit_rate = calculate_percentage(l1d_cache.access_hits, l1d_cache.access_total)
        l1d_miss_rate = calculate_percentage(l1d_cache.access_misses, l1d_cache.access_total)
        l1i_hit_rate = calculate_percentage(l1i_cache.access_hits, l1i_cache.access_total)
        l1i_miss_rate = calculate_percentage(l1i_cache.access_misses, l1i_cache.access_total)
        l1_total_miss_rate = calculate_percentage(l1d_cache.access_misses + l1i_cache.access_misses,
                                                  l1d_cache.access_total + l1i_cache.access_total)
        l2_hit_rate = calculate_percentage(l2_cache.access_hits, l2_cache.access_total)
        l2_miss_rate = calculate_percentage(l2_cache.access_misses, l2_cache.access_total)
        amat = l1i_cache.hit_time + (l1_total_miss_rate / 100) * (
                    l2_cache.hit_time + (l2_miss_rate / 100) * l2_cache.miss_penalty)

        # print(f"L1 Data Hits: {l1d_cache.access_hits} ({l1d_hit_rate:.2f}) Total: {l1d_cache.access_total}")
        # print(f"L1 Data Misses: {l1d_cache.access_misses} ({l1d_miss_rate:.2f})")
        # print(f"L1 Instruction Hits: {l1i_cache.access_hits} ({l1i_hit_rate:.2f}) Total: {l1i_cache.access_total}")
        # print(f"L1 Instruction Misses: {l1i_cache.access_misses} ({l1i_miss_rate:.2f})")
        # print(f"L2 Hits: {l2_cache.access_hits} ({l2_hit_rate:.2f}) Total: {l2_cache.access_total}")
        # print(f"L2 Misses: {l2_cache.access_misses} ({l2_miss_rate:.2f})")
        # print(f"AMAT: {amat:.2f}\n")
        print(f"|{l2_cache.set_associativity:13}|{l1i_cache.access_total:13}|{l1i_cache.access_misses:13}|{l1i_hit_rate:12.2f}%|{l1d_cache.access_total:13}|{l1d_cache.access_misses:13}|{l1d_hit_rate:12.2f}%|{l2_cache.access_total:13}|{l2_cache.access_misses:13}|{l2_hit_rate:12.2f}%|{amat:13.2f}|")
        print("|"+('-' * 13 + "|")*11)
        if (stats != None):
            stats[0].append(l1i_hit_rate)
            stats[1].append(l1d_hit_rate)
            stats[2].append(l2_hit_rate)
            stats[3].append(amat)

def simulate_cache(cache_type, trace_file_path):
    cache_sizes = [1024, 16384]
    block_sizes = [32, 128]
    associativities = [1, 2, 4, 8, 16, 32]
    associativities_l2 = [1, 4, 16, 32, 64, 128]
    l1_cache_sizes = [1024, 2048, 4096, 8192, 16384]
    l1_block_sizes = [8, 16, 32, 64, 128]
    l2_cache_sizes = [4096, 8192, 16384, 32768, 65536]

    l1_hit = 1
    l2_hit = 10
    miss_penalty = 100

    if cache_type == "Part2-WriteThrough":
        print(f"******{cache_type}******")
        print("|" + ('-' * 15 + "|")*8)
        print(f'|{"Assoc. Level":15}|{"L1I accesses":15}|{"L1I misses":15}|{"L1I hit rate":15}|{"L1D accesses":15}|{"L1D misses":15}|{"L1D hit rate":15}|{"AMAT":15}|')
        print("|" + ('-' * 15 + "|")*8)
        for cache_associativity in associativities:
            l1d_cache = WriteThroughCache(cache_sizes[0], block_sizes[0], cache_associativity, l1_hit, miss_penalty,None)
            l1i_cache = WriteThroughCache(cache_sizes[0], block_sizes[0], cache_associativity, l1_hit, miss_penalty, None)
            # print(f"****Instruction: {l1i_cache.access_hits}, Data: {l1d_cache.access_hits}")
            simulate_l1_cache(l1d_cache, l1i_cache, trace_file_path)
            # print(f"****Instruction: {l1i_cache.access_hits}, Data: {l1d_cache.access_hits}")
    elif cache_type == "Part4-WriteBack":
        print(f"******{cache_type}******")
        print("|" + ('-' * 15 + "|")*8)
        print(f'|{"Assoc. Level":15}|{"L1I accesses":15}|{"L1I misses":15}|{"L1I hit rate":15}|{"L1D accesses":15}|{"L1D misses":15}|{"L1D hit rate":15}|{"AMAT":15}|')
        print("|" + ('-' * 15 + "|")*8)
        for cache_associativity in associativities:
            l1d_cache = WriteBackCache(cache_sizes[0], block_sizes[0], cache_associativity, l1_hit, miss_penalty, None)
            l1i_cache = WriteBackCache(cache_sizes[0], block_sizes[0], cache_associativity, l1_hit, miss_penalty, None)
            simulate_l1_cache(l1d_cache, l1i_cache, trace_file_path)
    elif cache_type == "Part5-WriteBack with L2":
        print(f"******{cache_type}******")
        print("|"+('-' * 13 + "|")*11)
        print(f'|{"Assoc. Level":13}|{"L1I accesses":13}|{"L1I misses":13}|{"L1I hit rate":13}|{"L1D accesses":13}|{"L1D misses":13}|{"L1D hit rate":13}|{"L2 accesses":13}|{"L2 misses":13}|{"L2 hit rate":13}|{"AMAT":13}|')
        print("|"+('-' * 13 + "|")*11)
        for cache_associativity in associativities_l2:
            l2_cache = WriteBackCache(cache_sizes[1], block_sizes[1], cache_associativity, l2_hit, miss_penalty, None)
            l1d_cache = WriteBackCache(cache_sizes[0], block_sizes[0], 2, l1_hit, miss_penalty, l2_cache)
            l1i_cache = WriteBackCache(cache_sizes[0], block_sizes[0], 2, l1_hit, miss_penalty, l2_cache)
            simulate_l1_l2_cache(l1d_cache, l1i_cache, l2_cache, trace_file_path, None)
    elif cache_type == "Part6-Data Collection":
        l1i_hit_rates = []
        l1d_hit_rates = []
        l2_hit_rates = []
        amats = []
        stats = [l1i_hit_rates, l1d_hit_rates, l2_hit_rates, amats]
        print(f"******{cache_type}******")
        print("****** Varying L1 cache size ****** ")
        print("|"+('-' * 13 + "|")*11)
        print(f'|{"Assoc. Level":13}|{"L1I accesses":13}|{"L1I misses":13}|{"L1I hit rate":13}|{"L1D accesses":13}|{"L1D misses":13}|{"L1D hit rate":13}|{"L2 accesses":13}|{"L2 misses":13}|{"L2 hit rate":13}|{"AMAT":13}|')
        print("|"+('-' * 13 + "|")*11)
        for cache_size in l1_cache_sizes:
            l2_cache = WriteBackCache(cache_sizes[1], block_sizes[1], 8, l2_hit, miss_penalty, None)
            l1d_cache = WriteBackCache(cache_size, block_sizes[0], 2, l1_hit, miss_penalty, l2_cache)
            l1i_cache = WriteBackCache(cache_size, block_sizes[0], 2, l1_hit, miss_penalty, l2_cache)
            simulate_l1_l2_cache(l1d_cache, l1i_cache, l2_cache, trace_file_path, stats)
        
        # Plotting L1 Cache Size variations
        plt.plot(l1_cache_sizes, stats[0], marker='o', label='L1 Data Hit Rate')
        plt.plot(l1_cache_sizes, stats[1], marker='o', label='L1 Instruction Hit Rate')
        plt.plot(l1_cache_sizes, stats[2], marker='o', label='L2 Hit Rate')
        plt.plot(l1_cache_sizes, stats[3], marker='o', label='AMAT')
        plt.xlabel('L1 Cache Size (bytes)')
        plt.ylabel('Percentage(%) or AMAT(cycle)')
        plt.title('Cache Performance with Varying L1 Cache Size')
        plt.legend()
        plt.show()
        #########################################################################################
        l1i_hit_rates = []
        l1d_hit_rates = []
        l2_hit_rates = []
        amats = []
        stats = [l1i_hit_rates, l1d_hit_rates, l2_hit_rates, amats]
        print("****** Varying L1 block size ****** ")
        print("|"+('-' * 13 + "|")*11)
        print(f'|{"Assoc. Level":13}|{"L1I accesses":13}|{"L1I misses":13}|{"L1I hit rate":13}|{"L1D accesses":13}|{"L1D misses":13}|{"L1D hit rate":13}|{"L2 accesses":13}|{"L2 misses":13}|{"L2 hit rate":13}|{"AMAT":13}|')
        print("|"+('-' * 13 + "|")*11)
        for block_size in l1_block_sizes:
            l2_cache = WriteBackCache(cache_sizes[1], block_sizes[1], 8, l2_hit, miss_penalty, None)
            l1d_cache = WriteBackCache(cache_sizes[0], block_size, 2, l1_hit, miss_penalty, l2_cache)
            l1i_cache = WriteBackCache(cache_sizes[0], block_size, 2, l1_hit, miss_penalty, l2_cache)
            simulate_l1_l2_cache(l1d_cache, l1i_cache, l2_cache, trace_file_path, stats)
        # Plotting L1 Block Size variations
        plt.plot(l1_block_sizes, stats[0], marker='o', label='L1 Data Hit Rate')
        plt.plot(l1_block_sizes, stats[1], marker='o', label='L1 Instruction Hit Rate')
        plt.plot(l1_block_sizes, stats[2], marker='o', label='L2 Hit Rate')
        plt.plot(l1_block_sizes, stats[3], marker='o', label='AMAT')
        plt.xlabel('L1 Block Size (bytes)')
        plt.ylabel('Percentage(%) or AMAT(cycle)')
        plt.title('Cache Performance with Varying L1 Block Size')
        plt.legend()
        plt.show()
        #########################################################################################    
        l1i_hit_rates = []
        l1d_hit_rates = []
        l2_hit_rates = []
        amats = []
        stats = [l1i_hit_rates, l1d_hit_rates, l2_hit_rates, amats]
        print("****** Varying L2 cache size ****** ")
        print("|"+('-' * 13 + "|")*11)
        print(f'|{"Assoc. Level":13}|{"L1I accesses":13}|{"L1I misses":13}|{"L1I hit rate":13}|{"L1D accesses":13}|{"L1D misses":13}|{"L1D hit rate":13}|{"L2 accesses":13}|{"L2 misses":13}|{"L2 hit rate":13}|{"AMAT":13}|')
        print("|"+('-' * 13 + "|")*11)
        for cache_size in l2_cache_sizes:
            l2_cache = WriteBackCache(cache_size, block_sizes[1], 8, l2_hit, miss_penalty, None)
            l1d_cache = WriteBackCache(cache_sizes[0], block_sizes[0], 2, l1_hit, miss_penalty, l2_cache)
            l1i_cache = WriteBackCache(cache_sizes[0], block_sizes[0], 2, l1_hit, miss_penalty, l2_cache)
            simulate_l1_l2_cache(l1d_cache, l1i_cache, l2_cache, trace_file_path, stats)
        # Plotting L2 Cache Size variations
        plt.plot(l2_cache_sizes, stats[0], marker='o', label='L1 Data Hit Rate')
        plt.plot(l2_cache_sizes, stats[1], marker='o', label='L1 Instruction Hit Rate')
        plt.plot(l2_cache_sizes, stats[2], marker='o', label='L2 Hit Rate')
        plt.plot(l2_cache_sizes, stats[3], marker='o', label='AMAT')
        plt.xlabel('L2 Cache Size (bytes)')
        plt.ylabel('Percentage(%) or AMAT(cycle)')
        plt.title('Cache Performance with Varying L2 Cache Size')
        plt.legend()
        plt.show()

def main():
    print("Select the cache simulation:")
    print("1. Write-Through Cache (Part 1 & 2)")
    print("2. Write-Back Cache (Part 3 & 4)")
    print("3. Two Cache Levels (Part 5)")
    print("4. Part6-Data Collection ")

    choice = input("Enter your choice (1, 2, 3 or 4): ")
    pathA = "C:/Users/quang/Desktop/GradClass/Learning/CS529-Com_Architecture/Project/traces/cc.trace"
    pathB = "C:/Users/quang/Desktop/GradClass/Learning/CS529-Com_Architecture/Project/traces/spice.trace"
    pathC = "C:/Users/quang/Desktop/GradClass/Learning/CS529-Com_Architecture/Project/traces/tex.trace"
    file_path = [pathA, pathB, pathC]

    for path in file_path:
        print(f"File name: {os.path.basename(path)}")
        if choice == "1":
            simulate_cache("Part2-WriteThrough", path)
            # print('-' * 140)
        elif choice == "2":
            simulate_cache("Part4-WriteBack", path)
            # print('-' * 140)
        elif choice == "3":
            simulate_cache("Part5-WriteBack with L2", path)
            # print('-' * 140)
        elif choice == "4":
            simulate_cache("Part6-Data Collection", path)
            # print('-' * 140)
        else:
            print("Invalid choice. Please enter either 1, 2, 3 or 4.")


if __name__ == "__main__":
    main()
<script setup lang="ts">
import { ref, onMounted } from 'vue'

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8088').replace(/\/$/, '')

// Define the shape of our data
interface CpuSpec {
  socket: string
  core_count: number
  thread_count: number
  base_clock_ghz: number
  boost_clock_ghz: number
}

interface Component {
  id: number
  brand: string
  model: string
  msrp: string
  cpu_spec: CpuSpec
}

const cpus = ref<Component[]>([])
const loading = ref(true)

// Fetch data from Django when the page loads
onMounted(async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/cpus/`)
    cpus.value = await response.json()
  } catch (error) {
    console.error('Error fetching CPUs:', error)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <main style="padding: 2rem; font-family: sans-serif; background: #1e1e1e; color: white; min-height: 100vh;">
    <h1>PC Builder - CPU Inventory</h1>
    
    <div v-if="loading">Loading hardware...</div>
    
    <div v-else style="display: grid; gap: 1rem; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));">
      <!-- Loop through the 80 CPUs -->
      <div v-for="cpu in cpus" :key="cpu.id" style="background: #2d2d2d; padding: 1rem; border-radius: 8px;">
        <h2 style="margin: 0 0 0.5rem 0; color: #42b883;">{{ cpu.brand }} {{ cpu.model }}</h2>
        <p style="margin: 0; font-size: 1.2rem; font-weight: bold;">${{ cpu.msrp }}</p>
        
        <ul style="color: #aaa; font-size: 0.9rem; padding-left: 1.2rem;">
          <li>Socket: {{ cpu.cpu_spec.socket }}</li>
          <li>Cores/Threads: {{ cpu.cpu_spec.core_count }}C / {{ cpu.cpu_spec.thread_count }}T</li>
          <li>Base Clock: {{ cpu.cpu_spec.base_clock_ghz }} GHz</li>
        </ul>
      </div>
    </div>
  </main>
</template>
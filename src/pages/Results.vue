<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { invoke } from "@tauri-apps/api/core";
import { Folder, RefreshCw, ChevronLeft, Download } from "lucide-vue-next";

// Types
interface SessionFolder {
  id: string;
  name: string;
  createdTime: string;
}

interface ResultRow {
  form_name: string;
  timestamp?: string;
  [key: string]: any;
}

const sessions = ref<SessionFolder[]>([]);
const selectedSession = ref<SessionFolder | null>(null);
const resultsData = ref<ResultRow[]>([]);
const isLoading = ref(false);

async function fetchSessions() {
  isLoading.value = true;
  try {
    const res = await invoke<string>("list_sessions");
    const parsed = JSON.parse(res);
    if (parsed.status === "success") {
      sessions.value = parsed.sessions;
    }
  } catch (e) {
    console.error("Fetch sessions failed:", e);
  } finally {
    isLoading.value = false;
  }
}

async function viewSession(session: SessionFolder) {
  selectedSession.value = session;
  isLoading.value = true;
  try {
    const res = await invoke<string>("get_session_results", { folderId: session.id });
    const parsed = JSON.parse(res);
    if (parsed.status === "success") {
      resultsData.value = parsed.data;
    }
  } catch (e) {
    console.error("Fetch results failed:", e);
  } finally {
    isLoading.value = false;
  }
}

const columns = computed(() => {
  if (resultsData.value.length === 0) return [];
  const firstRow = resultsData.value[0];
  return Object.keys(firstRow).filter(k => k !== 'form_name' && k !== 'timestamp');
});

onMounted(fetchSessions);
</script>

<template>
  <div class="results-container">
    <header class="page-header">
      <div class="header-left">
        <button v-if="selectedSession" @click="selectedSession = null" class="btn-back">
          <ChevronLeft :size="20" />
        </button>
        <h1>{{ selectedSession ? selectedSession.name : 'Generated Sessions' }}</h1>
      </div>
      <button @click="fetchSessions" class="refresh-btn" :disabled="isLoading">
        <RefreshCw :size="20" :class="{ 'spin': isLoading }" />
      </button>
    </header>

    <div v-if="!selectedSession" class="session-grid">
      <div v-for="s in sessions" :key="s.id" class="session-card" @click="viewSession(s)">
        <Folder class="folder-icon" :size="32" />
        <div class="session-info">
          <h3>{{ s.name }}</h3>
          <p>{{ new Date(s.createdTime).toLocaleDateString() }}</p>
        </div>
      </div>
    </div>

    <div v-else class="table-view">
      <div class="scroll-area">
        <table v-if="resultsData.length">
          <thead>
            <tr>
              <th>Form Source</th>
              <th v-for="col in columns" :key="col">{{ col }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in resultsData" :key="i">
              <td class="bold-cell">{{ row.form_name }}</td>
              <td v-for="col in columns" :key="col">{{ row[col] || '-' }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state">No responses found yet.</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Fixed: Ensured block is not empty to avoid Vite crash */
.results-container {
  padding: 2rem;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: white;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.session-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1.5rem;
}

.session-card {
  padding: 1.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.session-card:hover {
  border-color: #6366f1;
  background: #f5f3ff;
}

.folder-icon {
  color: #6366f1;
  margin-bottom: 0.5rem;
}

.scroll-area {
  flex: 1;
  overflow: auto;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

th {
  background: #f8fafc;
  padding: 12px;
  text-align: left;
  border-bottom: 2px solid #e2e8f0;
  position: sticky;
  top: 0;
}

td {
  padding: 12px;
  border-bottom: 1px solid #f1f5f9;
}

.bold-cell {
  font-weight: 600;
  color: #6366f1;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
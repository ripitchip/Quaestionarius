<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { readDir, readTextFile, mkdir, BaseDirectory } from '@tauri-apps/plugin-fs';
import { 
  FileJson, 
  Eye, 
  Trash2, 
  LayoutTemplate, 
  Info, 
  ChevronRight, 
  Plus, 
  RefreshCw, 
  FolderOpen 
} from 'lucide-vue-next';

interface Template { 
  name: string; 
  filename: string; 
  content: any; 
}

const templates = ref<Template[]>([]);
const selectedTemplate = ref<Template | null>(null);
const isLoading = ref(true);

async function loadTemplates() {
  isLoading.value = true;
  try {
    // Ensures 'templates' folder exists in official AppData
    await mkdir('templates', { baseDir: BaseDirectory.AppData, recursive: true });
    
    const entries = await readDir('templates', { baseDir: BaseDirectory.AppData });
    const loaded: Template[] = [];
    
    for (const entry of entries) {
      if (entry.name && entry.name.endsWith('.json')) {
        const raw = await readTextFile(`templates/${entry.name}`, { baseDir: BaseDirectory.AppData });
        const json = JSON.parse(raw);
        loaded.push({
          name: json.name || entry.name.replace('.json', ''),
          filename: entry.name,
          content: json
        });
      }
    }
    templates.value = loaded;
  } catch (e) {
    console.error("FS Error:", e);
  } finally {
    isLoading.value = false;
  }
}

onMounted(loadTemplates);
</script>

<template>
  <div class="manager-container">
    <aside class="template-sidebar">
      <div class="sidebar-header">
        <div class="brand">
          <LayoutTemplate :size="18" />
          <h2>Templates</h2>
        </div>
        <div class="actions">
          <button class="btn-icon" @click="loadTemplates" :disabled="isLoading">
            <RefreshCw :size="16" :class="{ 'spin': isLoading }" />
          </button>
          <button class="btn-icon"><Plus :size="16" /></button>
        </div>
      </div>

      <div v-if="templates.length === 0" class="empty-list">
        <FolderOpen :size="32" />
        <p>No templates in AppData</p>
      </div>
      
      <div v-else class="template-list">
        <div 
          v-for="tpl in templates" 
          :key="tpl.filename" 
          class="template-item" 
          :class="{ active: selectedTemplate?.filename === tpl.filename }" 
          @click="selectedTemplate = tpl"
        >
          <FileJson :size="16" />
          <div class="item-info">
            <span class="tpl-name">{{ tpl.name }}</span>
            <span class="tpl-file">{{ tpl.filename }}</span>
          </div>
          <ChevronRight :size="14" class="chevron" />
        </div>
      </div>
    </aside>

    <main class="preview-area">
      <div v-if="selectedTemplate" class="preview-card">
         <header class="preview-header">
            <div>
              <h1>{{ selectedTemplate.name }}</h1>
              <p class="file-meta">Source: {{ selectedTemplate.filename }}</p>
            </div>
            <button class="btn-danger">
              <Trash2 :size="16" />
              Delete
            </button>
         </header>
         <div class="preview-body">
            <section class="logic-info">
              <h3><Info :size="14" /> Template Logic</h3>
              <p>Raw JSON structure for form generation:</p>
            </section>
            <pre><code>{{ JSON.stringify(selectedTemplate.content, null, 2) }}</code></pre>
         </div>
      </div>
      <div v-else class="empty-preview">
        <Eye :size="48" />
        <p>Select a template to preview</p>
      </div>
    </main>
  </div>
</template>

<style scoped>
.manager-container { display: flex; height: 100vh; background: #f8fafc; overflow: hidden; }
.template-sidebar { width: 320px; background: white; border-right: 1px solid #e2e8f0; display: flex; flex-direction: column; }

.sidebar-header { 
  padding: 1.25rem 1rem; 
  border-bottom: 1px solid #f1f5f9; 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
}
.brand { display: flex; align-items: center; gap: 8px; }
.brand h2 { font-size: 0.9rem; font-weight: 700; margin: 0; }

.actions { display: flex; gap: 4px; }
.btn-icon { 
  padding: 6px; 
  background: transparent; 
  border: none; 
  border-radius: 6px; 
  cursor: pointer; 
  color: #64748b;
}
.btn-icon:hover { background: #f1f5f9; color: #6366f1; }

.template-list { padding: 8px; flex: 1; overflow-y: auto; }
.template-item { 
  display: flex; 
  align-items: center; 
  gap: 12px; 
  padding: 10px; 
  border-radius: 8px; 
  cursor: pointer; 
  transition: all 0.2s;
  margin-bottom: 4px;
}
.template-item:hover { background: #f8fafc; }
.template-item.active { background: #6366f1; color: white; }
.item-info { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.tpl-name { font-size: 0.85rem; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tpl-file { font-size: 0.7rem; opacity: 0.7; }
.chevron { opacity: 0.5; }

.preview-area { flex: 1; padding: 2rem; overflow-y: auto; background: #f8fafc; }
.preview-card { background: white; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.preview-header { padding: 1.5rem; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: start; }
.preview-header h1 { margin: 0; font-size: 1.25rem; }
.file-meta { margin: 4px 0 0; font-size: 0.8rem; color: #94a3b8; }

.btn-danger {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fee2e2;
  color: #ef4444;
  border: none;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
}

.preview-body { padding: 1.5rem; }
.logic-info h3 { display: flex; align-items: center; gap: 6px; font-size: 0.9rem; margin-top: 0; }
pre { background: #1e293b; color: #94a3b8; padding: 1.5rem; border-radius: 12px; font-size: 0.8rem; overflow-x: auto; }

.empty-list, .empty-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  text-align: center;
}
.empty-list { padding: 3rem 1rem; }
.empty-preview { height: 100%; }

.spin { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
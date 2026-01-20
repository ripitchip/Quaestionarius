<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { readDir, readTextFile, mkdir, BaseDirectory } from '@tauri-apps/plugin-fs';
import { 
  FileJson, Eye, Trash2, LayoutTemplate, Info, 
  ChevronRight, Plus, RefreshCw, FolderOpen 
} from 'lucide-vue-next';

interface Template { 
  name: string; 
  filename: string; 
  content: any; 
}

const templates = ref<Template[]>([]);
const selectedTemplate = ref<Template | null>(null);
const isLoading = ref(true);

// --- Mock Data Constants ---
const MOCK_COLLEAGUES = ["Alex Johnson", "Maria Garcia", "Sam Smith"];

// --- Helper Functions ---

const formatMockText = (text: string | undefined): string => {
  if (!text) return '';
  return text
    .replace(/\{\{group_name\}\}/g, 'Marketing Team')
    .replace(/\{\{member_name\}\}/g, 'John Doe')
    .replace(/\{\{max_value\}\}/g, '5')
    .replace(/\{\{colleague_name\}\}/g, MOCK_COLLEAGUES[0]);
};

const getMockColumns = (columns: any): { value: string }[] => {
  if (columns?.options === "{{range_list}}") {
    return Array.from({ length: 6 }, (_, i) => ({ value: i.toString() }));
  }
  if (Array.isArray(columns?.options)) return columns.options;
  return [{ value: "Column 1" }];
};

const getMockRows = (rows: any): string[] => {
  if (rows?.options === "{{colleagues_list}}") return MOCK_COLLEAGUES;
  if (Array.isArray(rows?.options)) return rows.options.map((o: any) => o.value);
  return ["Sample Row 1"];
};

/**
 * Check if the request is a repeated text input per colleague
 */
const isRepeatedText = (req: any) => {
  return req.repeat_for === "{{colleagues_list}}" && req.createItem?.item?.questionItem?.question?.textQuestion;
};

const getGrid = (item: any) => {
  return item?.questionItem?.question?.gridQuestion || null;
};

const detectedVariables = computed(() => {
  if (!selectedTemplate.value) return [];
  const str = JSON.stringify(selectedTemplate.value.content);
  const vars = [];
  if (str.includes('{{group_name}}')) vars.push('group_name');
  if (str.includes('{{member_name}}')) vars.push('member_name');
  if (str.includes('{{colleagues_list}}')) vars.push('colleagues_list');
  if (str.includes('{{max_value}}')) vars.push('max_value');
  if (str.includes('{{range_list}}')) vars.push('range_list');
  return vars;
});

async function loadTemplates() {
  isLoading.value = true;
  try {
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
    if (loaded.length > 0 && !selectedTemplate.value) selectedTemplate.value = loaded[0];
  } catch (e) {
    console.error("FS Error:", e);
  } finally {
    isLoading.value = false;
  }
}

onMounted(loadTemplates);
</script>

<template>
  <div class="app-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="brand">
          <LayoutTemplate :size="20" class="brand-icon" />
          <h1>Templates</h1>
        </div>
        <button class="btn-refresh" @click="loadTemplates" :disabled="isLoading">
          <RefreshCw :size="16" :class="{ 'spin': isLoading }" />
        </button>
      </div>

      <div v-if="templates.length === 0" class="empty-nav">
        <FolderOpen :size="32" />
        <p>No JSON files found</p>
      </div>

      <div v-else class="nav-list">
        <div 
          v-for="tpl in templates" 
          :key="tpl.filename" 
          class="nav-item" 
          :class="{ active: selectedTemplate?.filename === tpl.filename }"
          @click="selectedTemplate = tpl"
        >
          <FileJson :size="16" />
          <div class="nav-details">
            <span class="nav-title">{{ tpl.name }}</span>
            <span class="nav-meta">{{ tpl.filename }}</span>
          </div>
          <ChevronRight :size="14" class="chevron" />
        </div>
      </div>
    </aside>

    <main class="main-viewer">
      <div v-if="selectedTemplate" class="viewer-container">
        
        <header class="viewer-header">
          <div class="header-info">
            <h2>{{ selectedTemplate.name }}</h2>
            <div class="tag-row">
              <span v-for="v in detectedVariables" :key="v" class="tag">{{ v }}</span>
            </div>
          </div>
          <button class="btn-delete"><Trash2 :size="16" /> Remove</button>
        </header>

        <div class="viewer-split">
          <section class="pane simulator">
            <div class="pane-title"><Eye :size="14" /> Google Forms Preview</div>
            <div class="form-canvas">
              <div class="form-theme-bar"></div>
              
              <div v-for="(req, idx) in selectedTemplate.content.requests" :key="idx">
                
                <template v-if="isRepeatedText(req)">
                  <div class="form-card header-card">
                    <h3 class="mock-title">{{ formatMockText(req.createItem.item.title) }}</h3>
                    <p class="mock-description">{{ formatMockText(req.createItem.item.description) }}</p>
                  </div>
                  
                  <div v-for="name in MOCK_COLLEAGUES" :key="name" class="form-card">
                    <div class="question-block">
                      <label class="mock-q-label">How many potatoes for <strong>{{ name }}</strong>?</label>
                      <div class="mock-text-field">
                        <span class="placeholder">Short answer text</span>
                        <div class="line"></div>
                      </div>
                      <div class="validation-msg">Must be a whole number between 0 and 5</div>
                    </div>
                  </div>
                </template>

                <div v-else-if="req.createItem" class="form-card">
                  <div class="question-block">
                    <h3 class="mock-title">{{ formatMockText(req.createItem.item.title) }}</h3>
                    <p class="mock-description">{{ formatMockText(req.createItem.item.description) }}</p>

                    <div v-if="getGrid(req.createItem.item)" class="mock-grid">
                      <table>
                        <thead>
                          <tr>
                            <th></th>
                            <th v-for="col in getMockColumns(getGrid(req.createItem.item).columns)" :key="col.value">
                              {{ col.value }}
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="row in getMockRows(getGrid(req.createItem.item).rows)" :key="row">
                            <td class="row-label">{{ row }}</td>
                            <td v-for="col in getMockColumns(getGrid(req.createItem.item).columns)" :key="col.value">
                              <div class="mock-check radio"></div>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>

                    <div v-else-if="req.createItem.item.questionItem?.question?.textQuestion" class="mock-text-field">
                      <span class="placeholder">Short answer text</span>
                      <div class="line"></div>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </section>

          <section class="pane source">
            <div class="pane-title"><Info :size="14" /> Raw Source</div>
            <div class="code-box">
              <pre><code>{{ JSON.stringify(selectedTemplate.content, null, 2) }}</code></pre>
            </div>
          </section>
        </div>
      </div>

      <div v-else class="empty-viewer">
        <LayoutTemplate :size="64" />
        <p>Select a template from the list to preview logic</p>
      </div>
    </main>
  </div>
</template>

<style scoped>
.app-layout { display: flex; height: 100vh; background: #fff; overflow: hidden; font-family: system-ui, sans-serif; }
.sidebar { width: 280px; border-right: 1px solid #e5e7eb; display: flex; flex-direction: column; }
.main-viewer { flex: 1; background: #f9fafb; display: flex; flex-direction: column; overflow: hidden; }

.sidebar-header { padding: 1.25rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f3f4f6; }
.brand { display: flex; align-items: center; gap: 8px; }
.brand h1 { font-size: 1rem; font-weight: 700; margin: 0; }
.brand-icon { color: #673ab7; }

.nav-list { flex: 1; overflow-y: auto; padding: 0.75rem; }
.nav-item { display: flex; align-items: center; gap: 12px; padding: 10px; border-radius: 8px; cursor: pointer; transition: 0.2s; margin-bottom: 4px; color: #4b5563; }
.nav-item:hover { background: #f3f4f6; }
.nav-item.active { background: #ede9fe; color: #5b21b6; }
.nav-details { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.nav-title { font-weight: 600; font-size: 0.875rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.nav-meta { font-size: 0.75rem; opacity: 0.6; }

.viewer-header { padding: 1.5rem 2rem; background: #fff; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center; }
.tag { background: #f3f4f6; color: #6b7280; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 600; border: 1px solid #e5e7eb; }

.viewer-split { display: grid; grid-template-columns: 1fr 380px; gap: 1.5rem; padding: 1.5rem; flex: 1; overflow: hidden; }
.pane { display: flex; flex-direction: column; }
.pane-title { font-size: 0.75rem; font-weight: 700; color: #9ca3af; margin-bottom: 0.75rem; text-transform: uppercase; display: flex; align-items: center; gap: 6px; }

/* Simulator (Google Forms Style) */
.form-canvas { background: #f0ebf8; border-radius: 8px; border: 1px solid #d1c4e9; flex: 1; overflow-y: auto; padding: 16px; }
.form-theme-bar { height: 10px; background: #673ab7; border-radius: 8px 8px 0 0; margin: -16px -16px 16px -16px; }

.form-card { background: #fff; border-radius: 8px; padding: 24px; margin-bottom: 12px; border: 1px solid #dadce0; }
.header-card { border-top: 8px solid #673ab7; }

.mock-title { font-size: 1.5rem; font-weight: 400; margin: 0 0 8px 0; color: #202124; }
.mock-description { font-size: 0.875rem; color: #70757a; margin-bottom: 24px; }
.mock-q-label { display: block; margin-bottom: 16px; font-size: 1rem; color: #202124; }

/* Numeric Text Inputs */
.mock-text-field { width: 50%; padding-top: 8px; position: relative; }
.placeholder { color: #70757a; font-size: 0.9rem; }
.line { height: 1px; background: #dadce0; margin-top: 8px; }
.validation-msg { color: #70757a; font-size: 0.75rem; margin-top: 8px; }

/* Grid styles */
.mock-grid table { width: 100%; border-collapse: collapse; }
.mock-grid th { font-size: 0.75rem; color: #70757a; padding: 12px; text-align: center; }
.row-label { text-align: left; font-size: 0.875rem; width: 40%; }
.mock-check.radio { width: 18px; height: 18px; border: 2px solid #dadce0; border-radius: 50%; margin: 0 auto; }

.code-box { background: #1e293b; border-radius: 8px; flex: 1; overflow: auto; }
pre { margin: 0; padding: 1rem; color: #94a3b8; font-size: 0.75rem; line-height: 1.6; }

.spin { animation: rotate 1s linear infinite; }
@keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
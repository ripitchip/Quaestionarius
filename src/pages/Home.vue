<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";
import { readFile, readDir, readTextFile, BaseDirectory } from "@tauri-apps/plugin-fs";
import { 
  Trash2, UploadCloud, Users, Mail, Hash, 
  FileJson, Play, Eye, CheckCircle2, Settings2, X, Loader2
} from "lucide-vue-next";
import Papa from "papaparse";

interface Participant {
  Name: string; LastName: string; Email: string; Group: string; id?: string;
}

interface Template {
  name: string; filename: string; content: any;
}

const csvData = ref<Participant[]>([]);
const fileName = ref("");
const templates = ref<Template[]>([]);
const selectedTemplate = ref<Template | null>(null);
const isPreviewing = ref(false);
const isGenerating = ref(false);

// Variable Discovery
const templateVars = ref<Record<string, string>>({});
const previewGroupIndex = ref(0);
const RESERVED_VARS = ['full_team_list', 'group_name', 'member_name'];

/**
 * Scans JSON for variables and pre-fills the bilingual proposition
 */
const scanVariables = () => {
  if (!selectedTemplate.value) return;
  const content = selectedTemplate.value.content;
  const str = JSON.stringify(content);
  const regex = /\{\{(.+?)\}\}/g;
  const found: Record<string, string> = {};
  let match;

  while ((match = regex.exec(str)) !== null) {
    const varName = match[1];
    if (!RESERVED_VARS.includes(varName)) {
      found[varName] = varName === 'max_value' ? (templateVars.value[varName] || "10") : (templateVars.value[varName] || "");
    }
  }

  if (content.proposition && found['prompt_text'] !== undefined) {
      found['prompt_text'] = content.proposition;
  }
  templateVars.value = found;
};

watch(selectedTemplate, scanVariables);

const groupedParticipants = computed(() => {
  return csvData.value.reduce((acc, person) => {
    const g = person.Group || "General";
    if (!acc[g]) acc[g] = [];
    acc[g].push(person);
    return acc;
  }, {} as Record<string, Participant[]>);
});

const groupNames = computed(() => Object.keys(groupedParticipants.value));
const currentPreviewGroup = computed(() => groupNames.value[previewGroupIndex.value]);

const formatPreviewText = (text: string | undefined) => {
  if (!text || !currentPreviewGroup.value) return '';
  let res = text.replace(/\{\{group_name\}\}/g, currentPreviewGroup.value);
  Object.keys(templateVars.value).forEach(v => {
    const regex = new RegExp(`\\{\\{${v}\\}\\}`, 'g');
    res = res.replace(regex, templateVars.value[v] || `[${v}]`);
  });
  return res;
};

// --- API ACTIONS ---

async function handleGenerate() {
  if (!selectedTemplate.value || isGenerating.value) return;

  isGenerating.value = true;
  try {
    // 1. Create Folders and Forms in Google Drive
    const genResult: string = await invoke("start_batch_generation", {
      templateName: selectedTemplate.value.filename,
      groupDataJson: JSON.stringify(groupedParticipants.value),
      variablesJson: JSON.stringify(templateVars.value)
    });

    const parsedGen = JSON.parse(genResult);
    
    if (parsedGen.status === "success") {
      // 2. Check for SMTP settings
      const emailSettingsRaw: string = await invoke("get_email_settings");
      
      if (emailSettingsRaw && emailSettingsRaw !== "{}") {
        try {
          // 3. Trigger Email Sequence via Sidecar
          const emailResult: string = await invoke("send_emails", {
            emailSettingsJson: emailSettingsRaw,
            groupDataJson: JSON.stringify(groupedParticipants.value),
            formResultsJson: JSON.stringify(parsedGen.forms)
          });

          const parsedEmail = JSON.parse(emailResult);
          
          if (parsedEmail.status === "success") {
            alert(`Success! Generated ${parsedGen.forms.length} forms and sent notification emails.`);
          } else {
            alert(`Forms created, but emails failed: ${parsedEmail.message}`);
          }
        } catch (emailErr) {
          alert("Error triggering email sidecar: " + emailErr);
        }
      } else {
        alert(`Forms generated! (SMTP not configured, emails skipped).`);
      }
    } else {
      alert("Generation Error: " + parsedGen.message);
    }
  } catch (error) {
    alert("Process failed: " + error);
  } finally {
    isGenerating.value = false;
  }
}

async function handleFileImport() {
  try {
    const selected = await open({ multiple: false, filters: [{ name: "CSV", extensions: ["csv"] }] });
    if (!selected || Array.isArray(selected)) return;
    fileName.value = selected.split(/[\\/]/).pop() || "";
    const contents = await readFile(selected);
    parseCsv(new TextDecoder("utf-8").decode(contents));
    loadTemplates();
  } catch (e) { console.error(e); }
}

function parseCsv(content: string) {
  Papa.parse(content, {
    header: true, 
    skipEmptyLines: true,
    complete: (r) => {
      csvData.value = r.data.map((row: any) => ({
        Name: row.Name || "Unknown", 
        LastName: row.LastName || "",
        Email: row.Email || "", // Correctly pulls from CSV column
        Group: row.Group || "General",
        id: row.id || Math.floor(Math.random() * 1000).toString()
      }));
    },
  });
}

async function loadTemplates() {
  try {
    const entries = await readDir('templates', { baseDir: BaseDirectory.AppData });
    const loaded: Template[] = [];
    for (const e of entries) {
      if (e.name?.endsWith('.json')) {
        const raw = await readTextFile(`templates/${e.name}`, { baseDir: BaseDirectory.AppData });
        const json = JSON.parse(raw);
        loaded.push({ name: json.name || e.name, filename: e.name, content: json });
      }
    }
    templates.value = loaded;
  } catch (e) { console.error(e); }
}

const reset = () => { csvData.value = []; fileName.value = ""; selectedTemplate.value = null; };
onMounted(loadTemplates);
</script>

<template>
  <div class="page-container">
    <header class="page-header">
      <div class="header-text">
        <h1>Dashboard</h1>
        <div v-if="csvData.length" class="meta-row">
          <span class="pill-badge"><Users :size="12" /> {{ csvData.length }} Entries</span>
          <span class="pill-badge">👥 {{ groupNames.length }} Teams</span>
        </div>
      </div>
      <div v-if="csvData.length" class="active-file-tag">
        <span class="filename-text">{{ fileName }}</span>
        <button class="btn-clear" @click="reset"><Trash2 :size="12" /></button>
      </div>
    </header>

    <div v-if="!csvData.length" class="upload-hero" @click="handleFileImport">
      <div class="hero-inner">
        <div class="icon-blob"><UploadCloud :size="32" /></div>
        <h2>Import Participant CSV</h2>
      </div>
    </div>

    <div v-else class="main-content">
      <div class="carousel-viewport">
        <div v-for="(members, g) in groupedParticipants" :key="g" class="group-card">
          <div class="card-head">
            <h3 class="group-label">{{ g }}</h3>
            <span class="count-tag">{{ members.length }}</span>
          </div>
          <div class="member-scroller">
            <div v-for="p in members" :key="p.id" class="member-tile">
              <div class="avatar-box">{{ p.Name[0] }}{{ p.LastName[0] }}</div>
              <div class="text-stack">
                <span class="full-name">{{ p.Name }} {{ p.LastName }}</span>
                <span class="email-sub">{{ p.Email }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="config-grid">
        <div class="config-pane">
          <div class="section-label">1. Choose Template</div>
          <div class="template-list">
            <div v-for="tpl in templates" :key="tpl.filename" 
                 class="tpl-option" :class="{ active: selectedTemplate?.filename === tpl.filename }"
                 @click="selectedTemplate = tpl">
              <CheckCircle2 v-if="selectedTemplate?.filename === tpl.filename" :size="14" />
              <FileJson v-else :size="14" />
              <span>{{ tpl.name }}</span>
            </div>
          </div>
        </div>

        <div class="config-pane">
          <div class="section-label">2. Define Parameters</div>
          <div v-if="Object.keys(templateVars).length" class="vars-list">
            <div v-for="(val, k) in templateVars" :key="k" class="var-field">
              <label><Settings2 :size="12" /> {{ k.replace('_', ' ') }}</label>
              <textarea v-if="k === 'prompt_text'" v-model="templateVars[k]" rows="4"></textarea>
              <input v-else type="text" v-model="templateVars[k]" />
            </div>
          </div>
          <div v-else class="var-empty">Select a template</div>
        </div>
      </div>

      <transition name="slide-up">
        <div v-if="selectedTemplate" class="action-bar">
          <div class="action-info">
            <p>Ready to generate <b>{{ groupNames.length }}</b> shared team forms.</p>
            <span class="sub-label">Includes Email Identification field for submittors.</span>
          </div>
          <div class="action-btns">
            <button class="btn-preview" @click="isPreviewing = true" :disabled="isGenerating"><Eye :size="16" /> Preview Simulation</button>
            <button class="btn-launch" :disabled="isGenerating || Object.values(templateVars).some(v => !v)" @click="handleGenerate">
              <Loader2 v-if="isGenerating" :size="16" class="spin-icon" />
              <span v-else>Generate & Email</span>
            </button>
          </div>
        </div>
      </transition>
    </div>

    <div v-if="isPreviewing" class="modal-overlay">
      <div class="modal-window">
        <header class="modal-header">
          <div class="modal-title-group">
            <h3>Google Form Simulation</h3>
            <div class="user-switcher">
              <span>Preview Team:</span>
              <select v-model="previewGroupIndex">
                <option v-for="(name, i) in groupNames" :key="name" :value="i">{{ name }}</option>
              </select>
            </div>
          </div>
          <button class="close-btn" @click="isPreviewing = false"><X :size="20" /></button>
        </header>

        <div class="modal-body">
          <div class="google-form-mock">
            <div class="form-accent"></div>
            
            <div class="mock-card head-card">
              <h1 class="mock-title">Team Evaluation: {{ currentPreviewGroup }}</h1>
              <p class="mock-desc">{{ formatPreviewText(templateVars['prompt_text']) }}</p>
            </div>

            <div class="mock-card id-card">
              <div class="mock-q">
                <label class="req">Veuillez entrer votre adresse courriel / Please enter your email address</label>
                <div class="mock-input-field">Your answer</div>
              </div>
            </div>

            <div v-for="p in groupedParticipants[currentPreviewGroup]" :key="p.id" class="mock-card">
              <div class="mock-q">
                <label>Potatoes for <b>{{ p.Name }} {{ p.LastName }}</b>?</label>
                <div class="mock-input-field">Short answer text</div>
                <div class="mock-validation">Scale: 0 - {{ templateVars['max_value'] || '10' }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-container { height: 100vh; display: flex; flex-direction: column; padding: 1.25rem; overflow: hidden; background: #fff; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
h1 { font-size: 1.25rem; font-weight: 800; }

.upload-hero { margin-top: 2rem; flex: 0 0 250px; border: 2px dashed #cbd5e1; border-radius: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; background: #f8fafc; transition: 0.2s; }
.upload-hero:hover { border-color: #6366f1; background: #f5f3ff; }

.carousel-viewport { display: flex; gap: 1rem; overflow-x: auto; padding: 5px 0 15px 0; scroll-snap-type: x mandatory; }
.group-card { flex: 0 0 260px; scroll-snap-align: start; background: white; border: 1px solid #e2e8f0; border-radius: 14px; height: 320px; display: flex; flex-direction: column; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
.card-head { padding: 12px; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center; background: #f8fafc; border-radius: 14px 14px 0 0; }

.member-scroller { flex: 1; overflow-y: auto; padding: 10px; display: flex; flex-direction: column; gap: 8px; }
.member-tile { display: flex; align-items: center; gap: 10px; padding: 8px; background: #fcfcfc; border-radius: 8px; border: 1px solid #f1f5f9; }
.avatar-box { width: 32px; height: 32px; background: #ede9fe; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 0.65rem; font-weight: 800; color: #6366f1; }
.text-stack { display: flex; flex-direction: column; }
.full-name { font-size: 0.8rem; font-weight: 600; }
.email-sub { font-size: 0.65rem; color: #94a3b8; }

.config-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem; }
.config-pane { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 1.25rem; min-height: 180px; display: flex; flex-direction: column; }
.section-label { font-size: 0.7rem; font-weight: 800; color: #94a3b8; text-transform: uppercase; margin-bottom: 1rem; }

.template-list { display: flex; flex-direction: column; gap: 4px; }
.tpl-option { display: flex; align-items: center; gap: 10px; padding: 10px; border-radius: 8px; cursor: pointer; font-size: 0.85rem; font-weight: 600; color: #64748b; transition: 0.2s; }
.tpl-option.active { background: #ede9fe; color: #6366f1; }

.var-field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
.var-field label { font-size: 0.7rem; font-weight: 700; color: #64748b; text-transform: uppercase; }
.var-field input, .var-field textarea { background: #f8fafc; border: 1px solid #e2e8f0; padding: 10px; border-radius: 10px; font-size: 0.85rem; outline: none; }
.var-field textarea { resize: none; }

.action-bar { margin-top: auto; background: #1e1e2d; color: white; border-radius: 16px; padding: 1.25rem; display: flex; justify-content: space-between; align-items: center; }
.btn-launch { background: #6366f1; color: white; border: none; padding: 12px 24px; border-radius: 10px; font-weight: 800; cursor: pointer; display: flex; align-items: center; gap: 10px; }
.btn-launch:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-preview { background: transparent; border: 1px solid #3f3f4f; color: #94a3b8; padding: 10px 18px; border-radius: 10px; cursor: pointer; display: flex; align-items: center; gap: 8px; font-size: 0.85rem; }

.modal-overlay { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(4px); z-index: 2000; display: flex; align-items: center; justify-content: center; }
.modal-window { background: #f0ebf8; width: 90%; max-width: 650px; height: 85vh; border-radius: 24px; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); }
.modal-header { background: white; padding: 1.25rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; }
.modal-body { flex: 1; overflow-y: auto; padding: 2rem; }

.google-form-mock { width: 100%; max-width: 500px; margin: 0 auto; }
.form-accent { height: 10px; background: #673ab7; border-radius: 8px 8px 0 0; }
.mock-card { background: white; padding: 24px; border-radius: 8px; border: 1px solid #dadce0; margin-bottom: 12px; }
.id-card { border-left: 6px solid #673ab7; }
.mock-title { font-size: 1.6rem; margin-bottom: 8px; }
.mock-desc { font-size: 0.95rem; color: #202124; line-height: 1.5; }
.mock-input-field { border-bottom: 1px solid #dadce0; color: #70757a; font-size: 0.9rem; padding: 8px 0; width: 70%; margin-top: 12px; }
.req::after { content: " *"; color: #d93025; }

.spin-icon { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.active-file-tag { display: flex; align-items: center; gap: 10px; background: #f8fafc; padding: 6px 12px; border-radius: 10px; border: 1px solid #e2e8f0; }
.filename-text { font-size: 0.8rem; font-weight: 700; color: #6366f1; }
</style>
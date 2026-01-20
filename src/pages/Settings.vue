<script setup lang="ts">
import { ref, onMounted } from "vue";
import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";
import { 
  FileJson, Save, Link, CheckCircle2, AlertCircle, 
  Loader2, Mail, ShieldCheck, Server 
} from "lucide-vue-next";

// --- ORIGINAL REFS ---
const jsonFilePath = ref("");
const jsonFileName = ref("");
const jsonOutput = ref("");
const jsonLoading = ref(false);
const jsonError = ref("");
const credentialsStatus = ref("");
const credentialsStatusType = ref<"info" | "success" | "warning" | "">("");
const authStatus = ref("Loading...");
const authLoading = ref(false);
const isAuthenticated = ref(false);

// --- NEW EMAIL REFS ---
const emailSettings = ref({
  smtp_server: "",
  smtp_port: "587",
  smtp_user: "",
  smtp_password: "",
});
const emailStatus = ref("");
const emailLoading = ref(false);

onMounted(async () => {
  try {
    await new Promise(resolve => setTimeout(resolve, 800));
    await checkAuthStatus();
    await loadEmailSettings();
  } catch (e) {
    console.error("Auth check error:", e);
  }
});

// --- NEW EMAIL ACTIONS ---
async function loadEmailSettings() {
  try {
    const result = await invoke("get_email_settings");
    if (result) {
      const parsed = JSON.parse(String(result));
      emailSettings.value = { ...emailSettings.value, ...parsed };
    }
  } catch (e) {
    console.warn("No email settings found");
  }
}

async function saveEmailConfig() {
  emailLoading.value = true;
  emailStatus.value = "";
  try {
    const result = await invoke("save_email_settings", { 
      settings: JSON.stringify(emailSettings.value) 
    });
    emailStatus.value = "✓ Email settings saved";
  } catch (e) {
    emailStatus.value = "Failed to save settings";
  } finally {
    emailLoading.value = false;
  }
}

// --- ORIGINAL LOGIC KEPT EXACTLY AS IT WAS ---
async function checkAuthStatus() {
  try {
    const result = await invoke("check_auth_status");
    const response = JSON.parse(String(result));
    if (response.status === "authenticated") {
      isAuthenticated.value = true;
      authStatus.value = "✓ Authenticated with Google";
    } else if (response.status === "expired") {
      isAuthenticated.value = false;
      authStatus.value = "⚠ Token expired, please re-authenticate";
    } else {
      isAuthenticated.value = false;
      authStatus.value = response.has_credentials ? "Ready to authenticate" : "Please save credentials first";
    }
  } catch (e) {
    authStatus.value = "Ready to start";
  }
}

async function openJsonFile() {
  try {
    jsonError.value = "";
    const file = await open({ filters: [{ name: "JSON", extensions: ["json"] }] });
    if (!file) return;
    jsonFilePath.value = file as string;
    jsonFileName.value = (file as string).split(/[\\/]/).pop() || "";
    await processJson();
  } catch (e) { jsonError.value = `Failed to open file: ${String(e)}`; }
}

async function processJson() {
  if (!jsonFilePath.value) return;
  jsonLoading.value = true;
  try {
    const result = await invoke("validate_credentials_file", { filePath: jsonFilePath.value });
    jsonOutput.value = String(result);
  } catch (e) { jsonError.value = String(e); } finally { jsonLoading.value = false; }
}

async function saveCredentials() {
  if (!jsonFilePath.value) return;
  try {
    credentialsStatus.value = "";
    const result = await invoke("save_credentials", { filePath: jsonFilePath.value });
    const response = JSON.parse(String(result));
    if (response.status === "success" || response.status === "updated") {
      credentialsStatus.value = `${response.message}`;
      credentialsStatusType.value = response.status === "success" ? "success" : "warning";
      await checkAuthStatus();
    }
  } catch (e) { jsonError.value = `Failed to save: ${String(e)}`; }
}

async function authenticateGoogle() {
  authLoading.value = true;
  try {
    const result = await invoke("authenticate_google");
    const response = JSON.parse(String(result));
    if (response.status === "success") await checkAuthStatus();
  } catch (e) { jsonError.value = `Auth failed: ${String(e)}`; } finally { authLoading.value = false; }
}
</script>

<template>
  <div class="settings-container page-container">
    <header class="page-header">
      <h1>Settings & Authentication</h1>
      <p class="subtitle">Connect your local machine to the Google Forms API Engine</p>
    </header>

    <div class="status-banner" :class="{ 'is-active': isAuthenticated }">
      <div class="status-content">
        <component :is="isAuthenticated ? CheckCircle2 : AlertCircle" class="status-icon" :size="20" />
        <span>{{ authStatus }}</span>
      </div>
    </div>

    <div class="settings-grid">
      <section class="settings-card">
        <div class="card-header">
          <div class="icon-box"><FileJson :size="20" /></div>
          <h2>Step 1: Credentials</h2>
        </div>
        <p class="description">Upload your Google Cloud <code>credentials.json</code> file.</p>
        <div class="action-zone">
          <button @click="openJsonFile" :disabled="jsonLoading" class="btn btn-outline">
            <Loader2 v-if="jsonLoading" class="spin" :size="18" />
            <span v-else>Select JSON</span>
          </button>
          <div v-if="jsonFileName" class="file-info">
            <span class="file-tag">{{ jsonFileName }}</span>
            <button @click="saveCredentials" :disabled="jsonLoading || credentialsStatusType === 'info'" class="btn btn-save">
              <Save :size="16" /> Save
            </button>
          </div>
        </div>
        <transition name="slide"><div v-if="credentialsStatus" :class="['msg', credentialsStatusType]">{{ credentialsStatus }}</div></transition>
        <div v-if="jsonError" class="msg error">{{ jsonError }}</div>
      </section>

      <section class="settings-card">
        <div class="card-header">
          <div class="icon-box auth-icon"><Link :size="20" /></div>
          <h2>Step 2: Access</h2>
        </div>
        <p class="description">Link your Google Account to authorize form processing.</p>
        <button @click="authenticateGoogle" :disabled="authLoading || isAuthenticated" class="btn btn-primary btn-full">
          <Loader2 v-if="authLoading" class="spin" :size="20" />
          <span v-else-if="isAuthenticated">Authorized Access</span>
          <span v-else>Connect Account</span>
        </button>
        <p class="hint">Your browser will open to complete the secure OAuth login.</p>
      </section>

      <section class="settings-card">
        <div class="card-header">
          <div class="icon-box email-icon"><Mail :size="20" /></div>
          <h2>Step 3: Email Delivery</h2>
        </div>
        <p class="description">Configure SMTP settings to notify team members automatically.</p>
        
        <div class="email-form">
          <div class="input-row">
            <div class="field">
              <label><Server :size="12" /> SMTP Server</label>
              <input v-model="emailSettings.smtp_server" placeholder="smtp.gmail.com" />
            </div>
            <div class="field port">
              <label>Port</label>
              <input v-model="emailSettings.smtp_port" placeholder="587" />
            </div>
          </div>
          <div class="field">
            <label>Username / Email</label>
            <input v-model="emailSettings.smtp_user" placeholder="admin@example.com" />
          </div>
          <div class="field">
            <label><ShieldCheck :size="12" /> App Password</label>
            <input v-model="emailSettings.smtp_password" type="password" placeholder="••••••••••••" />
          </div>
        </div>

        <button @click="saveEmailConfig" :disabled="emailLoading" class="btn btn-primary btn-full">
          <Loader2 v-if="emailLoading" class="spin" :size="18" />
          <span v-else>Save Email Config</span>
        </button>
        <div v-if="emailStatus" class="msg success">{{ emailStatus }}</div>
      </section>
    </div>
  </div>
</template>

<style scoped>
/* ALL ORIGINAL STYLES PRESERVED */
.settings-container { max-width: 900px; margin: 0 auto; }
.page-header { margin-bottom: 2rem; }
.page-header h1 { font-size: 1.8rem; font-weight: 700; margin: 0; }
.subtitle { color: var(--text-muted); margin-top: 0.5rem; }

.status-banner {
  background: #f1f5f9;
  border-radius: 12px;
  padding: 1rem 1.5rem;
  margin-bottom: 2rem;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
}
.status-banner.is-active {
  background: #f0fdf4;
  border-color: #bbf7d0;
  color: #166534;
}
.status-content { display: flex; align-items: center; gap: 12px; font-weight: 600; }
.status-icon { width: 20px; }

.settings-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
.settings-card {
  background: var(--card-bg);
  padding: 1.5rem;
  border-radius: 16px;
  box-shadow: var(--card-shadow);
  display: flex;
  flex-direction: column;
}
.card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 1rem; }
.card-header h2 { font-size: 1.1rem; margin: 0; font-weight: 600; }

.icon-box {
  width: 36px;
  height: 36px;
  background: #eff6ff;
  color: #3b82f6;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
}
.auth-icon { background: #fdf2f8; color: #db2777; }
.email-icon { background: #f0fdf4; color: #16a34a; }

.description { font-size: 0.9rem; color: var(--text-muted); line-height: 1.5; margin-bottom: 1.5rem; }

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  font-size: 0.9rem;
}
.btn-primary { background: #1e1e2d; color: white; }
.btn-primary:hover:not(:disabled) { background: #33334d; }
.btn-outline { background: white; border: 1px solid #e2e8f0; color: #475569; }
.btn-outline:hover { background: #f8fafc; }
.btn-save { background: #6366f1; color: white; padding: 6px 14px; }
.btn-full { width: 100%; margin-top: auto; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.action-zone { display: flex; flex-direction: column; gap: 12px; }
.file-info { display: flex; align-items: center; justify-content: space-between; background: #f8fafc; padding: 8px; border-radius: 8px; border: 1px dashed #cbd5e1; }
.file-tag { font-family: monospace; font-size: 0.8rem; color: #6366f1; }

.msg { margin-top: 1rem; padding: 10px; border-radius: 6px; font-size: 0.85rem; font-weight: 500; }
.msg.success { background: #dcfce7; color: #15803d; }
.msg.warning { background: #fef9c3; color: #a16207; }
.msg.info { background: #e0f2fe; color: #0369a1; }
.msg.error { background: #fee2e2; color: #b91c1c; }

/* NEW EMAIL FORM STYLES */
.email-form { display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px; }
.input-row { display: grid; grid-template-columns: 1fr 80px; gap: 10px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 0.7rem; font-weight: 700; color: #64748b; text-transform: uppercase; display: flex; align-items: center; gap: 4px; }
.field input { background: #f8fafc; border: 1px solid #e2e8f0; padding: 8px 12px; border-radius: 8px; font-size: 0.85rem; outline: none; transition: 0.2s; }
.field input:focus { border-color: #6366f1; background: white; }

.hint { font-size: 0.75rem; color: var(--text-muted); text-align: center; margin-top: 12px; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .settings-grid { grid-template-columns: 1fr; }
}

@media (prefers-color-scheme: dark) {
  .settings-card { background: #1a1a26; border: 1px solid #2d2d3d; }
  .status-banner { background: #1e1e2d; border-color: #2d2d3d; color: #94a3b8; }
  .status-banner.is-active { background: #064e3b; color: #a7f3d0; border-color: #065f46; }
  .btn-outline { background: #2d2d3d; border-color: #3f3f4f; color: #cbd5e1; }
  .file-info { background: #12121a; border-color: #2d2d3d; }
  .field input { background: #12121a; border-color: #2d2d3d; color: #cbd5e1; }
}
</style>
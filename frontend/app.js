"use strict";

const DEFAULT_API_URL = "http://127.0.0.1:8000";
const PAGE_SIZE = 10;
const STATUS_LABELS = {
  pending: "Pending",
  open: "Open",
  on_hold: "On hold",
  resolved: "Resolved",
  discarded: "Discarded",
};

const state = {
  apiUrl: localStorage.getItem("resolve_api_url") || DEFAULT_API_URL,
  token: sessionStorage.getItem("resolve_access_token") || "",
  user: null,
  tickets: [],
  page: 1,
  total: 0,
  statusFilter: "",
  selectedTicket: null,
  comments: [],
  aiSuggestion: "",
  currentView: "overview",
};

const byId = (id) => document.getElementById(id);
const authScreen = byId("auth-screen");
const appShell = byId("app-shell");
const dialog = byId("ticket-dialog");

function showToast(message, kind = "success") {
  const toast = document.createElement("div");
  toast.className = `toast ${kind}`;
  toast.textContent = message;
  byId("toast-region").append(toast);
  window.setTimeout(() => toast.remove(), 4400);
}

function setBusy(button, busy, busyLabel = "Working…") {
  if (!button) return;
  if (busy) {
    button.dataset.originalLabel = button.textContent.trim();
    button.textContent = busyLabel;
    button.disabled = true;
  } else {
    button.textContent = button.dataset.originalLabel || button.textContent;
    button.disabled = false;
  }
}

function normalizedApiUrl() {
  return state.apiUrl.trim().replace(/\/+$/, "");
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (state.token) headers.set("Authorization", `Bearer ${state.token}`);
  if (options.body !== undefined) headers.set("Content-Type", "application/json");
  let response;
  try {
    response = await fetch(`${normalizedApiUrl()}${path}`, {
      ...options,
      headers,
    });
  } catch {
    throw new Error(`The browser could not read a response from ${normalizedApiUrl()}. Confirm the backend is running, CORS allows this frontend origin, and check the backend terminal for errors.`);
  }

  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    if (response.status === 401 && state.token) {
      signOut(false);
      showToast("Your session expired. Please sign in again.", "error");
    }
    const detail = typeof body === "object" && body !== null
      ? (body.detail || body.message || JSON.stringify(body))
      : body;
    throw new Error(detail || `Request failed with status ${response.status}.`);
  }
  return body;
}

function setApiUrl(value) {
  const candidate = value.trim().replace(/\/+$/, "");
  let parsed;
  try {
    parsed = new URL(candidate);
  } catch {
    throw new Error("Enter a valid API URL, such as http://127.0.0.1:8000.");
  }
  if (!["http:", "https:"].includes(parsed.protocol)) {
    throw new Error("The API URL must use HTTP or HTTPS.");
  }
  state.apiUrl = candidate;
  localStorage.setItem("resolve_api_url", candidate);
}

function displayName() {
  return state.user?.name || state.user?.email || "Your account";
}

function prettyRole(role) {
  return ({ user: "Customer", support_agent: "Support agent", admin: "Administrator" })[role] || role || "Member";
}

function initials(text) {
  return (text || "R").trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
}

function statusBadge(status) {
  const badge = document.createElement("span");
  badge.className = `status-badge status-${status}`;
  badge.textContent = STATUS_LABELS[status] || status || "Unknown";
  return badge;
}

function formatDate(value) {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? ""
    : new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
}

function switchAuthMode(mode) {
  const isLogin = mode === "login";
  byId("login-form").classList.toggle("hidden", !isLogin);
  byId("register-form").classList.toggle("hidden", isLogin);
  byId("show-login").classList.toggle("active", isLogin);
  byId("show-register").classList.toggle("active", !isLogin);
  byId("auth-title").textContent = isLogin ? "Welcome back" : "Create your account";
  byId("auth-subtitle").textContent = isLogin
    ? "Sign in to your support workspace."
    : "A few details and you’re ready to go.";
}

async function checkApi() {
  const stateLine = byId("api-state");
  stateLine.classList.remove("online", "offline");
  try {
    setApiUrl(byId("api-url").value);
    stateLine.lastChild.textContent = " Checking connection…";
    await request("/");
    const database = await request("/db-test");
    if (database.message !== "Database connection successful") {
      throw new Error("The API is reachable, but the database connection failed.");
    }
    stateLine.classList.add("online");
    stateLine.lastChild.textContent = " API and database connected";
  } catch (error) {
    stateLine.classList.add("offline");
    stateLine.lastChild.textContent = ` ${error.message}`;
  }
}

function enterWorkspace(user) {
  state.user = user;
  authScreen.classList.add("hidden");
  appShell.classList.remove("hidden");
  byId("profile-name").textContent = displayName();
  byId("profile-role").textContent = prettyRole(user.role);
  byId("profile-avatar").textContent = initials(displayName());
  byId("account-name").textContent = displayName();
  byId("account-details").textContent = user.email || "";
  byId("account-role").textContent = prettyRole(user.role);
  byId("welcome-title").textContent = `Good to see you, ${displayName().split(" ")[0]}.`;
  byId("welcome-subtitle").textContent = user.role === "admin"
    ? "Here’s the support desk at a glance."
    : user.role === "support_agent"
      ? "Here are the tickets assigned to you."
      : "Here’s what’s happening with your tickets.";
  byId("admin-nav").classList.toggle("hidden", user.role !== "admin");
  byId("status-control").classList.toggle("hidden", user.role === "user");
  byId("delete-ticket").classList.toggle("hidden", user.role !== "admin");
  showView("overview");
  void loadTickets();
}

function signOut(notify = true) {
  state.token = "";
  state.user = null;
  sessionStorage.removeItem("resolve_access_token");
  appShell.classList.add("hidden");
  authScreen.classList.remove("hidden");
  if (dialog.open) dialog.close();
  if (notify) showToast("You’ve signed out.");
}

async function restoreSession() {
  byId("api-url").value = state.apiUrl;
  if (!state.token) return;
  try {
    state.user = await request("/user/me");
    enterWorkspace(state.user);
  } catch (error) {
    if (state.token) {
      signOut(false);
      showToast(error.message, "error");
    }
  }
}

function showView(view) {
  if (view === "admin" && state.user?.role !== "admin") {
    showToast("Admin access is required.", "error");
    return;
  }
  state.currentView = view;
  document.querySelectorAll(".page-view").forEach((element) => element.classList.add("hidden"));
  byId(`view-${view}`).classList.remove("hidden");
  document.querySelectorAll(".nav-item").forEach((element) => {
    element.classList.toggle("active", element.dataset.view === view);
  });
  const labels = { overview: "Overview", tickets: "Tickets", "new-ticket": "New ticket", admin: "Admin tools" };
  byId("page-label").textContent = labels[view] || "Overview";
}

function makeTicketRow(ticket) {
  const row = document.createElement("button");
  row.type = "button";
  row.className = "ticket-row";
  row.setAttribute("aria-label", `Open ticket ${ticket.id}: ${ticket.title}`);

  const main = document.createElement("span");
  main.className = "ticket-main";
  const title = document.createElement("b");
  title.textContent = ticket.title;
  const description = document.createElement("small");
  description.textContent = (ticket.desc || "").replace(/\s+/g, " ").slice(0, 110);
  main.append(title, description);

  const id = document.createElement("span");
  id.className = "ticket-id";
  id.textContent = `#${ticket.id}`;

  const owner = document.createElement("span");
  owner.className = "ticket-owner";
  owner.textContent = ticket.assigned_to ? `Agent #${ticket.assigned_to}` : `Customer #${ticket.user_id}`;
  const chevron = document.createElement("span");
  chevron.className = "ticket-chevron";
  chevron.textContent = "›";
  row.append(main, id, statusBadge(ticket.status), owner, chevron);
  row.addEventListener("click", () => void openTicket(ticket.id));
  return row;
}

function renderTicketList(target, tickets) {
  target.replaceChildren(...tickets.map(makeTicketRow));
}

async function loadTickets() {
  const query = new URLSearchParams({ page: String(state.page), limit: String(PAGE_SIZE) });
  if (state.statusFilter) query.set("status", state.statusFilter);
  const refreshButton = byId("refresh-button");
  setBusy(refreshButton, true, "Loading…");
  try {
    const result = await request(`/ticket?${query.toString()}`);
    state.tickets = Array.isArray(result.items) ? result.items : [];
    state.total = Number(result.total) || 0;
    state.page = Number(result.page) || state.page;
    byId("nav-ticket-count").textContent = String(state.total);
    renderTicketList(byId("ticket-list"), state.tickets);
    byId("tickets-empty").classList.toggle("hidden", state.tickets.length > 0);

    const recent = state.tickets.slice(0, 5);
    renderTicketList(byId("recent-ticket-list"), recent);
    byId("recent-empty").classList.toggle("hidden", state.tickets.length > 0);
    byId("stat-total").textContent = String(state.total);
    byId("stat-pending").textContent = String(state.tickets.filter((ticket) => ticket.status === "pending").length);
    byId("stat-progress").textContent = String(state.tickets.filter((ticket) => ["open", "on_hold"].includes(ticket.status)).length);
    byId("stat-resolved").textContent = String(state.tickets.filter((ticket) => ticket.status === "resolved").length);

    const first = state.total === 0 ? 0 : (state.page - 1) * PAGE_SIZE + 1;
    const last = Math.min(state.page * PAGE_SIZE, state.total);
    byId("page-summary").textContent = `Showing ${first}–${last} of ${state.total} tickets`;
    byId("page-prev").disabled = state.page <= 1;
    byId("page-next").disabled = last >= state.total;
    applyTicketSearch();
    byId("connection-state").classList.add("online");
    byId("connection-state").classList.remove("offline");
  } catch (error) {
    showToast(error.message, "error");
    byId("connection-state").classList.add("offline");
    byId("connection-state").classList.remove("online");
  } finally {
    setBusy(refreshButton, false);
  }
}

function applyTicketSearch() {
  const value = byId("ticket-search").value.trim().toLowerCase();
  const list = byId("ticket-list");
  const rows = [...list.children];
  rows.forEach((row, index) => {
    const ticket = state.tickets[index];
    const matches = !value || `${ticket.title} ${ticket.desc} ${ticket.id}`.toLowerCase().includes(value);
    row.classList.toggle("hidden", !matches);
  });
  const visibleCount = rows.some((row) => !row.classList.contains("hidden"));
  byId("tickets-empty").classList.toggle("hidden", visibleCount);
}

async function openTicket(ticketId) {
  try {
    const ticket = await request(`/ticket/${ticketId}`);
    state.selectedTicket = ticket;
    state.aiSuggestion = "";
    byId("ai-result").classList.add("hidden");
    byId("dialog-ticket-id").textContent = `TICKET #${ticket.id}`;
    byId("dialog-title").textContent = ticket.title;
    byId("dialog-status").className = `status-badge status-${ticket.status}`;
    byId("dialog-status").textContent = STATUS_LABELS[ticket.status] || ticket.status;
    byId("dialog-owner").textContent = `Customer #${ticket.user_id}`;
    byId("dialog-assignee").textContent = ticket.assigned_to ? `Assigned to agent #${ticket.assigned_to}` : "Unassigned";
    byId("dialog-description").textContent = ticket.desc;
    byId("ticket-status").value = ticket.status;
    byId("status-control").classList.toggle("hidden", state.user.role === "user");
    byId("delete-ticket").classList.toggle("hidden", state.user.role !== "admin");
    byId("reply-message").value = "";
    await loadComments(ticket.id);
    dialog.showModal();
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function loadComments(ticketId) {
  const comments = await request(`/ticket/${ticketId}/comments`);
  state.comments = Array.isArray(comments) ? comments : [];
  const list = byId("comment-list");
  if (state.comments.length === 0) {
    const empty = document.createElement("div");
    empty.className = "no-replies";
    empty.textContent = "No replies yet. Add the first message to this conversation.";
    list.replaceChildren(empty);
  } else {
    const bubbles = state.comments.map((comment) => {
      const bubble = document.createElement("article");
      bubble.className = `comment-bubble${comment.user_id === state.user.id ? " mine" : ""}`;
      const meta = document.createElement("div");
      meta.className = "comment-meta";
      const author = document.createElement("span");
      author.textContent = comment.user_id === state.user.id
        ? "You"
        : `User #${comment.user_id}${comment.user_id === state.selectedTicket.user_id ? " · customer" : ""}`;
      const time = document.createElement("time");
      time.textContent = formatDate(comment.created_at);
      meta.append(author, time);
      const message = document.createElement("p");
      message.textContent = comment.message;
      bubble.append(meta, message);
      return bubble;
    });
    list.replaceChildren(...bubbles);
  }
  byId("reply-count").textContent = `${state.comments.length} ${state.comments.length === 1 ? "reply" : "replies"}`;
}

async function submitLogin(form) {
  const submit = form.querySelector("button[type=submit]");
  setBusy(submit, true, "Signing in…");
  try {
    setApiUrl(byId("api-url").value);
    const values = Object.fromEntries(new FormData(form));
    const result = await request("/users/login", { method: "POST", body: JSON.stringify(values) });
    state.token = result.access_token;
    sessionStorage.setItem("resolve_access_token", state.token);
    const user = await request("/user/me");
    enterWorkspace(user);
    showToast(`Welcome back, ${user.name || "there"}.`);
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    setBusy(submit, false);
  }
}

async function submitRegistration(form) {
  const submit = form.querySelector("button[type=submit]");
  setBusy(submit, true, "Creating account…");
  try {
    setApiUrl(byId("api-url").value);
    const values = Object.fromEntries(new FormData(form));
    const result = await request("/users/register", { method: "POST", body: JSON.stringify(values) });
    showToast(`Account created. Your user ID is ${result.user_id}; sign in to continue.`);
    form.reset();
    switchAuthMode("login");
    byId("login-form").elements.email.value = values.email;
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    setBusy(submit, false);
  }
}

async function submitTicket(form) {
  const submit = form.querySelector("button[type=submit]");
  setBusy(submit, true, "Submitting…");
  try {
    const values = Object.fromEntries(new FormData(form));
    const result = await request("/ticket", { method: "POST", body: JSON.stringify(values) });
    form.reset();
    state.page = 1;
    showToast(`Ticket #${result.id} created.`);
    await loadTickets();
    showView("tickets");
    await openTicket(result.id);
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    setBusy(submit, false);
  }
}

async function submitReply(form) {
  if (!state.selectedTicket) return;
  const submit = form.querySelector("button[type=submit]");
  setBusy(submit, true, "Sending…");
  try {
    const values = Object.fromEntries(new FormData(form));
    await request(`/ticket/${state.selectedTicket.id}/comments`, {
      method: "POST",
      body: JSON.stringify(values),
    });
    form.reset();
    await loadComments(state.selectedTicket.id);
    showToast("Reply sent.");
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    setBusy(submit, false);
  }
}

async function updateTicketStatus() {
  if (!state.selectedTicket) return;
  const status = byId("ticket-status").value;
  try {
    const ticket = await request(`/ticket/${state.selectedTicket.id}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
    state.selectedTicket = ticket;
    byId("dialog-status").className = `status-badge status-${ticket.status}`;
    byId("dialog-status").textContent = STATUS_LABELS[ticket.status] || ticket.status;
    await loadTickets();
    showToast("Ticket status updated.");
  } catch (error) {
    byId("ticket-status").value = state.selectedTicket.status;
    showToast(error.message, "error");
  }
}

async function suggestAiReply() {
  if (!state.selectedTicket) return;
  const button = byId("ai-button");
  setBusy(button, true, "Thinking…");
  try {
    const result = await request(`/ticket/${state.selectedTicket.id}/ai-response`, { method: "POST" });
    state.aiSuggestion = result.response || "";
    byId("ai-text").textContent = state.aiSuggestion;
    byId("ai-result").classList.remove("hidden");
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    setBusy(button, false);
  }
}

async function deleteSelectedTicket() {
  if (!state.selectedTicket || !window.confirm(`Delete ticket #${state.selectedTicket.id}? This cannot be undone.`)) return;
  try {
    await request(`/ticket/${state.selectedTicket.id}`, { method: "DELETE" });
    dialog.close();
    showToast("Ticket deleted.");
    await loadTickets();
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function assignTicket(form) {
  const submit = form.querySelector("button[type=submit]");
  setBusy(submit, true, "Assigning…");
  try {
    const values = Object.fromEntries(new FormData(form));
    const ticketId = Number(values.ticket_id);
    const agentId = Number(values.agent_id);
    const result = await request(`/ticket/${ticketId}/assign?agent_id=${encodeURIComponent(agentId)}`, { method: "PATCH" });
    showToast(`Ticket #${result.ticket_id} assigned to agent #${result.assigned_to}.`);
    form.reset();
    await loadTickets();
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    setBusy(submit, false);
  }
}

async function updateRole(form) {
  const submit = form.querySelector("button[type=submit]");
  setBusy(submit, true, "Updating…");
  try {
    const values = Object.fromEntries(new FormData(form));
    const result = await request(`/users/${Number(values.user_id)}/role`, {
      method: "PATCH",
      body: JSON.stringify({ role: values.role }),
    });
    showToast(`User #${result.user_id} is now ${prettyRole(result.role)}.`);
    form.reset();
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    setBusy(submit, false);
  }
}

async function checkAdminAccess() {
  const button = byId("admin-check");
  const result = byId("admin-check-result");
  setBusy(button, true, "Checking…");
  result.textContent = "";
  result.style.color = "";
  try {
    const response = await request("/user/admin-test");
    result.textContent = response.message;
    showToast("Admin access confirmed.");
  } catch (error) {
    result.textContent = error.message;
    result.style.color = "#a7403d";
  } finally {
    setBusy(button, false);
  }
}

function bindEvents() {
  byId("show-login").addEventListener("click", () => switchAuthMode("login"));
  byId("show-register").addEventListener("click", () => switchAuthMode("register"));
  byId("login-form").addEventListener("submit", (event) => {
    event.preventDefault();
    void submitLogin(event.currentTarget);
  });
  byId("register-form").addEventListener("submit", (event) => {
    event.preventDefault();
    void submitRegistration(event.currentTarget);
  });
  byId("check-api").addEventListener("click", () => void checkApi());
  byId("logout-button").addEventListener("click", () => signOut());
  byId("mobile-logout").addEventListener("click", () => signOut());
  byId("refresh-button").addEventListener("click", () => void loadTickets());
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => showView(button.dataset.view));
  });
  document.querySelectorAll("[data-go]").forEach((button) => {
    button.addEventListener("click", () => showView(button.dataset.go));
  });
  byId("ticket-form").addEventListener("submit", (event) => {
    event.preventDefault();
    void submitTicket(event.currentTarget);
  });
  byId("comment-form").addEventListener("submit", (event) => {
    event.preventDefault();
    void submitReply(event.currentTarget);
  });
  byId("ticket-status").addEventListener("change", () => void updateTicketStatus());
  byId("ai-button").addEventListener("click", () => void suggestAiReply());
  byId("delete-ticket").addEventListener("click", () => void deleteSelectedTicket());
  byId("close-dialog").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
  byId("copy-ai").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(state.aiSuggestion);
      showToast("AI suggestion copied.");
    } catch {
      showToast("Could not copy to clipboard. Select and copy the suggestion instead.", "error");
    }
  });
  byId("use-ai").addEventListener("click", () => {
    byId("reply-message").value = state.aiSuggestion;
    byId("reply-message").focus();
  });
  byId("status-filter").addEventListener("change", (event) => {
    state.statusFilter = event.target.value;
    state.page = 1;
    void loadTickets();
  });
  byId("ticket-search").addEventListener("input", applyTicketSearch);
  byId("page-prev").addEventListener("click", () => {
    if (state.page > 1) {
      state.page -= 1;
      void loadTickets();
    }
  });
  byId("page-next").addEventListener("click", () => {
    if (state.page * PAGE_SIZE < state.total) {
      state.page += 1;
      void loadTickets();
    }
  });
  byId("assign-form").addEventListener("submit", (event) => {
    event.preventDefault();
    void assignTicket(event.currentTarget);
  });
  byId("role-form").addEventListener("submit", (event) => {
    event.preventDefault();
    void updateRole(event.currentTarget);
  });
  byId("admin-check").addEventListener("click", () => void checkAdminAccess());
}

bindEvents();
void restoreSession();

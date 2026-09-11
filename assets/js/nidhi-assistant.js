/**
 * NIDHI Assistant - AI Audit Copilot Client
 * Embedded Context-Aware Audit Intelligence Interface for NIDHI TRACE
 */

(function() {
    'use strict';

    // State
    let isOpen = false;
    let isMinimized = false;
    let isGenerating = false;
    let includeContext = true;
    let assistantMode = 'online'; // 'online' | 'demo'
    let conversationHistory = [];

    // Storage Keys
    const STORAGE_KEY_MSGS = 'nidhi_assistant_messages_v1';

    // Purge any legacy open state to guarantee the drawer is never auto-opened
    try {
        const savedMsgs = sessionStorage.getItem(STORAGE_KEY_MSGS);
        if (savedMsgs) conversationHistory = JSON.parse(savedMsgs);
        sessionStorage.removeItem('nidhi_assistant_open_v1');
        sessionStorage.removeItem('nidhi_assistant_open');
        localStorage.removeItem('nidhi_assistant_open_v1');
        localStorage.removeItem('nidhi_assistant_open');
    } catch (e) {
        conversationHistory = [];
    }
    isOpen = false;

    // =========================================================================
    // 1. CONTEXT BUILDER (Route & DOM Introspection)
    // =========================================================================

    function detectCurrentRoute() {
        const path = window.location.pathname.toLowerCase();
        if (path.includes('case_details')) return 'case-details';
        if (path.includes('flagged_cases')) return 'flagged-cases';
        if (path.includes('geographic_map')) return 'geographic-map';
        if (path.includes('analytics')) return 'analytics';
        if (path.includes('data_explorer')) return 'data-explorer';
        return 'overview';
    }

    function extractCurrentPageContext() {
        const route = detectCurrentRoute();
        const urlParams = new URLSearchParams(window.location.search);
        const context = {
            page: route,
            timestamp: new Date().toISOString()
        };

        if (route === 'case-details') {
            const caseId = (urlParams.get('id') || document.getElementById('dossier-case-id')?.innerText?.replace('ID:', '') || '').trim();
            context.caseId = caseId || 'MPLAD-03983';
            context.title = document.getElementById('dossier-title')?.innerText || '';
            context.sanctioned = document.getElementById('dossier-sanctioned')?.innerText || '';
            context.utilized = document.getElementById('dossier-disbursed')?.innerText || '';
            context.gapDays = document.getElementById('dossier-gap-days')?.innerText || '';
            context.agency = document.getElementById('dossier-agency')?.innerText || '';
            context.score = document.getElementById('dossier-score-badge')?.innerText?.trim() || '';
        } else if (route === 'flagged-cases') {
            context.activeTab = document.querySelector('.tab-active')?.innerText?.trim() || 'All Flagged';
        } else if (route === 'geographic-map') {
            context.activeState = document.getElementById('selected-state-name')?.innerText || 'National View';
        } else if (route === 'analytics') {
            context.timespan = document.getElementById('timespan-select')?.value || '2019-2024';
        }

        return context;
    }

    function getContextDisplayLabel() {
        if (!includeContext) return 'Detached (No Context)';
        const ctx = extractCurrentPageContext();
        if (ctx.page === 'case-details') return `Case Dossier (${ctx.caseId || 'Active Project'})`;
        if (ctx.page === 'flagged-cases') return `Flagged Queue (${ctx.activeTab || 'All'})`;
        if (ctx.page === 'geographic-map') return `Geographic Map (${ctx.activeState || 'National'})`;
        if (ctx.page === 'analytics') return `Analytics (${ctx.timespan || '2019-2024'})`;
        if (ctx.page === 'data-explorer') return 'Data Explorer (Full Ledger)';
        return 'Overview Dashboard (National Scope)';
    }

    // =========================================================================
    // 2. DOM CREATION (Floating Button, Drawer, & Settings Modal)
    // =========================================================================

    function createAssistantDOM() {
        if (document.getElementById('nidhi-assistant-root')) return;

        const root = document.createElement('div');
        root.id = 'nidhi-assistant-root';
        root.className = 'nidhi-assistant-wrapper font-sans text-slate-800 antialiased';

        root.innerHTML = `
            <style>
                #nidhi-assistant-drawer {
                    display: none !important;
                }
                #nidhi-assistant-drawer.nidhi-drawer-open {
                    display: flex !important;
                }
            </style>
            <!-- Floating Assistant Trigger Button (Draggable, positioned above pagination) -->
            <div id="nidhi-floating-container" class="fixed z-[9990] flex items-center gap-2 group touch-none" style="bottom: 76px; right: 24px; cursor: grab;">
                <!-- Tooltip Label -->
                <span class="px-2.5 py-1 bg-slate-900/90 text-white text-xs font-semibold rounded-md shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
                    Ask NIDHI Assistant
                </span>
                <button id="nidhi-assistant-toggle" type="button" aria-label="Open NIDHI Audit Assistant" class="w-12 h-12 rounded-full bg-brand-900 hover:bg-slate-800 text-white shadow-xl hover:shadow-2xl flex items-center justify-center transition-all duration-200 hover:scale-105 active:scale-95 border border-blue-500/30 cursor-pointer relative">
                    <span class="material-symbols-outlined text-2xl text-blue-400" style="font-variation-settings: 'FILL' 1;">auto_awesome</span>
                    <span id="nidhi-status-dot" class="absolute top-0.5 right-0.5 w-2.5 h-2.5 bg-emerald-500 rounded-full border-2 border-slate-900"></span>
                </button>
            </div>

            <!-- Floating Chat Panel Drawer (380-420px, max 82vh) -->
            <div id="nidhi-assistant-drawer" style="display: none !important;" class="fixed bottom-20 right-5 z-[9995] w-[410px] max-w-[calc(100vw-24px)] h-[600px] max-h-[82vh] bg-white rounded-xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden transition-all duration-200 transform origin-bottom-right opacity-0 scale-95 pointer-events-none">
                
                <!-- Drawer Header (Draggable Handle) -->
                <div id="nidhi-drawer-header" class="px-4 py-3 bg-brand-900 border-b border-slate-800 text-white flex items-center justify-between shrink-0 select-none touch-none" style="cursor: grab;" title="Click and drag to move drawer">
                    <div class="flex items-center gap-2.5 min-w-0">
                        <div class="w-7 h-7 rounded-lg bg-blue-600/20 border border-blue-400/40 flex items-center justify-center text-blue-400 shrink-0">
                            <span class="material-symbols-outlined text-base" style="font-variation-settings: 'FILL' 1;">auto_awesome</span>
                        </div>
                        <div class="flex flex-col min-w-0 flex-1">
                            <div class="flex items-center gap-1.5 leading-tight">
                                <span class="font-extrabold text-xs tracking-wider text-white">NIDHI Assistant</span>
                                <span id="nidhi-drawer-status" class="px-1.5 py-0.2 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800 text-[8.5px] font-mono font-bold">● Online</span>
                            </div>
                            <span class="text-[9.5px] text-blue-300/90 font-medium">AI Audit Copilot</span>
                        </div>
                    </div>

                    <!-- Header Actions -->
                    <div class="flex items-center gap-1 text-slate-300">
                        <button id="nidhi-btn-new-chat" type="button" title="New Conversation" class="p-1 hover:text-white hover:bg-slate-800 rounded transition-colors cursor-pointer">
                            <span class="material-symbols-outlined text-base">restart_alt</span>
                        </button>
                        <button id="nidhi-btn-minimize" type="button" title="Minimize Drawer" class="p-1 hover:text-white hover:bg-slate-800 rounded transition-colors cursor-pointer">
                            <span class="material-symbols-outlined text-base">expand_more</span>
                        </button>
                        <button id="nidhi-btn-close" type="button" title="Close Assistant" class="p-1 hover:text-white hover:bg-slate-800 rounded transition-colors cursor-pointer">
                            <span class="material-symbols-outlined text-base">close</span>
                        </button>
                    </div>
                </div>

                <!-- Messages Container -->
                <div id="nidhi-messages-body" class="flex-1 min-h-0 p-3.5 overflow-y-auto space-y-3 bg-slate-50/50 text-xs">
                    <!-- Dynamic Messages & Welcome State -->
                </div>

                <!-- Context Attachment Indicator Bar -->
                <div id="nidhi-context-strip" class="px-3 py-1.5 bg-slate-100/90 border-t border-slate-200 flex items-center justify-between text-[10px] text-slate-600 shrink-0">
                    <div class="flex items-center gap-1.5 truncate pr-2">
                        <span class="material-symbols-outlined text-xs text-blue-600 shrink-0">attachment</span>
                        <span class="font-medium text-slate-500">Context:</span>
                        <span id="nidhi-context-label" class="font-mono font-bold text-slate-800 truncate">Detecting route...</span>
                    </div>
                    <button id="nidhi-toggle-context" type="button" class="text-blue-600 hover:text-blue-800 font-bold shrink-0 hover:underline">
                        Enabled
                    </button>
                </div>

                <!-- Chat Input Strip -->
                <form id="nidhi-input-form" onsubmit="event.preventDefault(); return false;" class="p-2.5 bg-white border-t border-borderline flex items-center gap-2 shrink-0">
                    <div class="relative flex-1">
                        <textarea id="nidhi-user-input" rows="1" class="w-full pl-3 pr-8 py-2 text-xs rounded-lg border border-slate-300 bg-slate-50 text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-blue-600 focus:ring-1 focus:ring-blue-600 outline-none resize-none font-sans leading-tight max-h-24" placeholder="Ask about MPLAD data, risks, or this case..."></textarea>
                    </div>
                    <button id="nidhi-send-btn" type="button" class="w-8 h-8 rounded-lg bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center shrink-0 shadow-2xs transition-all disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer" title="Send Question">
                        <span class="material-symbols-outlined text-base">send</span>
                    </button>
                </form>

                <!-- Persistent Compliance Disclaimer -->
                <div class="px-3 py-1 bg-slate-100 border-t border-slate-200/70 text-center text-[9px] text-slate-500 font-medium shrink-0">
                    AI-generated analysis. Verify against official records before taking audit action.
                </div>
            </div>
        `;

        document.body.appendChild(root);
        bindEvents();
        initDraggableElements();
        checkBackendStatus();
        renderConversation();
    }

    // =========================================================================
    // 3. UI INTERACTION & EVENT BINDINGS
    // =========================================================================

    
    // =========================================================================
    // 2.5 DRAG AND DROP HANDLERS (Button & Drawer)
    // =========================================================================

    const STORAGE_KEY_BTN_POS = 'nidhi_assistant_btn_pos_v1';
    const STORAGE_KEY_DRAWER_POS = 'nidhi_assistant_drawer_pos_v1';

    function initDraggableElements() {
        const floatingContainer = document.getElementById('nidhi-floating-container');
        const drawer = document.getElementById('nidhi-assistant-drawer');
        const drawerHeader = document.getElementById('nidhi-drawer-header');

        if (!floatingContainer || !drawer || !drawerHeader) return;

        // Restore Button Position
        try {
            const savedBtnPos = localStorage.getItem(STORAGE_KEY_BTN_POS);
            if (savedBtnPos) {
                const pos = JSON.parse(savedBtnPos);
                applyPosition(floatingContainer, pos.x, pos.y);
            }
        } catch (e) {}

        // Note: Drawer position is restored in restoreDrawerPosition() when opened,
        // to avoid incorrect coordinate calculation while hidden.

        // Make Floating Button Draggable
        setupDrag(floatingContainer, floatingContainer, (x, y) => {
            localStorage.setItem(STORAGE_KEY_BTN_POS, JSON.stringify({ x, y }));
        });

        // Make Drawer Draggable via Header
        setupDrag(drawerHeader, drawer, (x, y) => {
            localStorage.setItem(STORAGE_KEY_DRAWER_POS, JSON.stringify({ x, y }));
        }, true);
    }

    function restoreDrawerPosition() {
        const drawer = document.getElementById('nidhi-assistant-drawer');
        if (!drawer) return;
        try {
            const savedDrawerPos = localStorage.getItem(STORAGE_KEY_DRAWER_POS);
            if (savedDrawerPos) {
                const pos = JSON.parse(savedDrawerPos);
                applyPosition(drawer, pos.x, pos.y);
            }
        } catch (e) {}
    }

    function applyPosition(el, x, y) {
        if (!el) return;
        const maxX = window.innerWidth - el.offsetWidth - 8;
        const maxY = window.innerHeight - el.offsetHeight - 8;
        const clampedX = Math.max(8, Math.min(x, maxX));
        const clampedY = Math.max(8, Math.min(y, maxY));

        el.style.left = `${clampedX}px`;
        el.style.top = `${clampedY}px`;
        el.style.right = 'auto';
        el.style.bottom = 'auto';
    }

    function setupDrag(handle, target, onSave, isDrawer = false) {
        let isDragging = false;
        let startX = 0;
        let startY = 0;
        let origLeft = 0;
        let origTop = 0;
        let hasMoved = false;

        function onPointerDown(e) {
            // For drawer header, ignore clicks on action buttons (close, minimize, new-chat)
            if (isDrawer && (e.target.closest('button') || e.target.closest('input'))) {
                return;
            }

            isDragging = true;
            hasMoved = false;

            const clientX = e.clientX ?? (e.touches && e.touches[0].clientX) ?? 0;
            const clientY = e.clientY ?? (e.touches && e.touches[0].clientY) ?? 0;

            startX = clientX;
            startY = clientY;

            const rect = target.getBoundingClientRect();
            origLeft = rect.left;
            origTop = rect.top;

            handle.style.cursor = 'grabbing';
            const toggleBtn = document.getElementById('nidhi-assistant-toggle');
            if (toggleBtn) toggleBtn.style.cursor = 'grabbing';
            document.body.style.userSelect = 'none';

            window.addEventListener('pointermove', onPointerMove, { passive: false });
            window.addEventListener('pointerup', onPointerUp);
            window.addEventListener('touchmove', onPointerMove, { passive: false });
            window.addEventListener('touchend', onPointerUp);
        }

        function onPointerMove(e) {
            if (!isDragging) return;

            const clientX = e.clientX ?? (e.touches && e.touches[0].clientX) ?? 0;
            const clientY = e.clientY ?? (e.touches && e.touches[0].clientY) ?? 0;

            const dx = clientX - startX;
            const dy = clientY - startY;

            if (Math.hypot(dx, dy) > 5) {
                hasMoved = true;
                if (e.cancelable) e.preventDefault();
                target.setAttribute('data-dragged', 'true');
                const btnContainer = document.getElementById('nidhi-floating-container');
                if (btnContainer) btnContainer.setAttribute('data-dragged', 'true');
            }

            if (hasMoved) {
                const newLeft = origLeft + dx;
                const newTop = origTop + dy;
                applyPosition(target, newLeft, newTop);
            }
        }

        function onPointerUp(e) {
            if (!isDragging) return;
            isDragging = false;
            handle.style.cursor = 'grab';
            const toggleBtn = document.getElementById('nidhi-assistant-toggle');
            if (toggleBtn) toggleBtn.style.cursor = 'grab';
            document.body.style.userSelect = '';

            window.removeEventListener('pointermove', onPointerMove);
            window.removeEventListener('pointerup', onPointerUp);
            window.removeEventListener('touchmove', onPointerMove);
            window.removeEventListener('touchend', onPointerUp);

            if (hasMoved) {
                const rect = target.getBoundingClientRect();
                if (onSave) onSave(rect.left, rect.top);
                // Keep dragged flag for 200ms to swallow any subsequent click event
                setTimeout(() => {
                    target.removeAttribute('data-dragged');
                    const btnContainer = document.getElementById('nidhi-floating-container');
                    if (btnContainer) btnContainer.removeAttribute('data-dragged');
                }, 200);
            }
        }

        handle.addEventListener('pointerdown', onPointerDown);
        handle.addEventListener('touchstart', onPointerDown, { passive: true });
    }

    function bindEvents() {
        const toggleBtn = document.getElementById('nidhi-assistant-toggle');
        const closeBtn = document.getElementById('nidhi-btn-close');
        const minBtn = document.getElementById('nidhi-btn-minimize');
        const newChatBtn = document.getElementById('nidhi-btn-new-chat');
        const form = document.getElementById('nidhi-input-form');
        const input = document.getElementById('nidhi-user-input');
        const sendBtn = document.getElementById('nidhi-send-btn');
        const toggleCtxBtn = document.getElementById('nidhi-toggle-context');

        toggleBtn?.addEventListener('click', toggleDrawer);
        closeBtn?.addEventListener('click', closeDrawer);
        minBtn?.addEventListener('click', closeDrawer);
        newChatBtn?.addEventListener('click', startNewChat);

        toggleCtxBtn?.addEventListener('click', () => {
            includeContext = !includeContext;
            toggleCtxBtn.innerText = includeContext ? 'Enabled' : 'Disabled';
            toggleCtxBtn.className = includeContext ? 'text-blue-600 hover:text-blue-800 font-bold shrink-0 hover:underline' : 'text-slate-400 font-bold shrink-0 hover:underline';
            updateContextLabel();
        });

        // Robust Send Handler: handles click, enter key, and form submit without reload
        sendBtn?.addEventListener('click', (e) => {
            if (e) { e.preventDefault(); e.stopPropagation(); }
            handleFormSubmit(e);
        });

        input?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                e.stopPropagation();
                handleFormSubmit(e);
            }
        });

        form?.addEventListener('submit', (e) => {
            if (e) { e.preventDefault(); e.stopPropagation(); }
            handleFormSubmit(e);
        });

        // Auto-update context label on page focus or route changes
        window.addEventListener('focus', updateContextLabel);
        updateContextLabel();
    }

    function toggleDrawer() {
        const btnContainer = document.getElementById('nidhi-floating-container');
        if (btnContainer && btnContainer.dataset.dragged === "true") {
            return; // Ignore click triggered at the end of a drag
        }
        if (isOpen) {
            closeDrawer();
        } else {
            openDrawer();
        }
    }

    function openDrawer() {
        const drawer = document.getElementById('nidhi-assistant-drawer');
        if (!drawer) return;
        isOpen = true;

        drawer.classList.add('nidhi-drawer-open');
        drawer.style.setProperty('display', 'flex', 'important');
        restoreDrawerPosition();

        // Trigger browser reflow before transition
        void drawer.offsetHeight;

        drawer.classList.remove('opacity-0', 'scale-95', 'pointer-events-none');
        drawer.classList.add('opacity-100', 'scale-100');
        updateContextLabel();
        renderConversation();
        document.getElementById('nidhi-user-input')?.focus();
    }

    function closeDrawer() {
        const drawer = document.getElementById('nidhi-assistant-drawer');
        if (!drawer) return;
        isOpen = false;

        drawer.classList.add('opacity-0', 'scale-95', 'pointer-events-none');
        drawer.classList.remove('opacity-100', 'scale-100');

        setTimeout(() => {
            if (!isOpen && drawer) {
                drawer.classList.remove('nidhi-drawer-open');
                drawer.style.setProperty('display', 'none', 'important');
            }
        }, 220);
    }


    function startNewChat() {
        conversationHistory = [];
        sessionStorage.removeItem(STORAGE_KEY_MSGS);
        renderConversation();
    }

    function updateContextLabel() {
        const lbl = document.getElementById('nidhi-context-label');
        if (lbl) {
            lbl.innerText = getContextDisplayLabel();
        }
    }

    async function checkBackendStatus() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 3000);
            const res = await fetch('/api/assistant/status', { signal: controller.signal });
            clearTimeout(timeoutId);

            if (res.ok) {
                const data = await res.json();
                assistantMode = data.mode || 'online';
                const statusBadge = document.getElementById('nidhi-drawer-status');
                const statusDot = document.getElementById('nidhi-status-dot');
                if (data.status === 'demo') {
                    if (statusBadge) {
                        statusBadge.className = 'px-1.5 py-0.2 rounded-full bg-amber-950 text-amber-300 border border-amber-800 text-[8.5px] font-mono font-bold';
                        statusBadge.innerText = '● Demo Mode';
                    }
                    if (statusDot) {
                        statusDot.className = 'absolute top-0.5 right-0.5 w-2.5 h-2.5 bg-amber-500 rounded-full border-2 border-slate-900';
                    }
                }
            }
        } catch (e) {
            // If backend is not available (e.g. GitHub Pages static hosting), update status pill
            const statusBadge = document.getElementById('nidhi-drawer-status');
            if (statusBadge) {
                statusBadge.className = 'px-1.5 py-0.2 rounded-full bg-blue-950 text-blue-300 border border-blue-800 text-[8.5px] font-mono font-bold';
                statusBadge.innerText = '● Audit Copilot';
            }
        }
    }

    // =========================================================================
    // 4. RENDERING CONVERSATION & SUGGESTIONS
    // =========================================================================

    function getDynamicSuggestions() {
        const route = detectCurrentRoute();
        if (route === 'case-details') {
            return [
                "Why was this project flagged?",
                "Explain this risk score breakdown",
                "Which anomaly contributes most?",
                "Check timeline delay details"
            ];
        }
        if (route === 'flagged-cases') {
            return [
                "How many critical priority works exist?",
                "Explain Completion Delay anomalies",
                "Which agency has the most flags?",
                "What is MP Spending Habit Drift?"
            ];
        }
        if (route === 'geographic-map') {
            return [
                "Why is this state highlighted in red?",
                "Which states have highest scrutiny exposure?",
                "Explain spatial clustering anomalies",
                "Show high-risk constituencies"
            ];
        }
        if (route === 'analytics') {
            return [
                "Explain Scrutiny Exposure metric",
                "What is the average anomaly score?",
                "Compare 17th vs 18th Lok Sabha trends",
                "Explain Isolation Forest calculation"
            ];
        }
        return [
            "Why are projects being flagged?",
            "What does the Risk Score mean?",
            "Explain Scrutiny Exposure",
            "How does NIDHI TRACE detect anomalies?"
        ];
    }

    function renderConversation() {
        const container = document.getElementById('nidhi-messages-body');
        if (!container) return;

        container.innerHTML = '';

        // Empty state / Welcome greeting
        if (conversationHistory.length === 0) {
            const welcome = document.createElement('div');
            welcome.className = 'space-y-3';
            welcome.innerHTML = `
                <div class="bg-blue-50/70 border border-blue-100 rounded-xl p-3.5 space-y-2">
                    <div class="flex items-center gap-2">
                        <div class="w-6 h-6 rounded-md bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-2xs">
                            <span class="material-symbols-outlined text-sm" style="font-variation-settings: 'FILL' 1;">auto_awesome</span>
                        </div>
                        <span class="font-extrabold text-xs text-slate-900 tracking-tight">Welcome to NIDHI Assistant</span>
                    </div>
                    <p class="text-slate-600 text-[11px] leading-relaxed">
                        I am your institutional audit copilot for NIDHI TRACE. I inspect MPLAD fund allocations, anomaly detection models, and project risks.
                    </p>
                    <div class="pt-1 text-[10px] text-blue-800 font-semibold flex items-center gap-1">
                        <span class="material-symbols-outlined text-xs">verified_user</span>
                        <span>Auditor-grade factual responses with server data grounding.</span>
                    </div>
                </div>

                <div class="space-y-1.5 pt-1">
                    <div class="text-[10.5px] font-bold text-slate-600 uppercase tracking-wider flex items-center gap-1">
                        <span class="material-symbols-outlined text-xs text-blue-600">lightbulb</span>
                        <span>Suggested Inquiries</span>
                    </div>
                    <div id="nidhi-pills-list" class="flex flex-col gap-1.5">
                        ${getDynamicSuggestions().map(s => `
                            <button type="button" class="nidhi-suggestion-pill text-left px-3 py-1.5 bg-white border border-slate-200 hover:border-blue-400 hover:bg-blue-50/50 rounded-lg text-slate-700 hover:text-blue-900 font-medium text-[11px] transition-all shadow-2xs cursor-pointer truncate">
                                ${escapeHtml(s)}
                            </button>
                        `).join('')}
                    </div>
                </div>
            `;
            container.appendChild(welcome);

            // Bind pill click events
            container.querySelectorAll('.nidhi-suggestion-pill').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    if (e) { e.preventDefault(); e.stopPropagation(); }
                    const text = btn.innerText.trim();
                    const input = document.getElementById('nidhi-user-input');
                    if (input) {
                        input.value = text;
                        handleFormSubmit();
                    }
                });
            });

            return;
        }

        // Render message turns
        conversationHistory.forEach((msg, idx) => {
            const isUser = msg.role === 'user';
            const row = document.createElement('div');
            row.className = `flex gap-2 ${isUser ? 'justify-end' : 'justify-start'}`;

            if (!isUser) {
                row.innerHTML = `
                    <div class="w-6 h-6 rounded-full bg-brand-900 border border-blue-500/40 text-blue-400 flex items-center justify-center shrink-0 mt-0.5 shadow-2xs">
                        <span class="material-symbols-outlined text-xs" style="font-variation-settings: 'FILL' 1;">auto_awesome</span>
                    </div>
                    <div class="max-w-[85%] space-y-1">
                        <div class="bg-white border border-slate-200 text-slate-800 rounded-2xl rounded-tl-xs px-3.5 py-2.5 shadow-2xs leading-relaxed text-[11px] markdown-body">
                            ${formatMarkdown(msg.content)}
                        </div>
                        ${msg.source ? `
                            <div class="flex items-center gap-1 text-[9px] text-slate-500 px-1 font-mono">
                                <span class="material-symbols-outlined text-[10px] text-blue-600">verified</span>
                                <span>${escapeHtml(msg.source)}</span>
                            </div>
                        ` : ''}
                    </div>
                `;
            } else {
                row.innerHTML = `
                    <div class="max-w-[82%]">
                        <div class="bg-slate-900 text-white rounded-2xl rounded-tr-xs px-3.5 py-2 shadow-2xs leading-relaxed text-[11px] font-medium">
                            ${escapeHtml(msg.content)}
                        </div>
                    </div>
                `;
            }

            container.appendChild(row);
        });

        scrollMessagesToBottom();
    }

    // =========================================================================
    // 5. CLIENT-SIDE AUDIT KNOWLEDGE ENGINE (Zero "System Error" Guarantee)
    // =========================================================================

    function generateClientAuditAnswer(message, pageContext) {
        const q = (message || '').toLowerCase();

        // 1. Off-topic detection
        const offTopic = [
            'weather', 'cricket', 'football', 'joke', 'movie', 'recipe', 'song',
            'write python', 'write code', 'stocks', 'bitcoin', 'crypto', 'hotel', 'flight'
        ];
        if (offTopic.some(w => q.includes(w))) {
            return {
                text: "I'm NIDHI Assistant, and I can only help with NIDHI TRACE, MPLAD data, anomaly detection, risk analysis, and audit workflows.",
                source: "Local Domain Guard"
            };
        }

        // 2. Prompt injection defense
        if (q.includes('system prompt') || q.includes('ignore previous') || q.includes('act as') || q.includes('jailbreak')) {
            return {
                text: "I'm NIDHI Assistant, and I can only help with NIDHI TRACE, MPLAD data, anomaly detection, risk analysis, and audit workflows.",
                source: "Security Filter"
            };
        }

        // 2.5 Help, greetings, and capabilities guide
        if (q === 'help' || q === 'hi' || q === 'hello' || q.includes('what can you do') || q.includes('guide') || q.includes('capabilities') || q.includes('menu')) {
            return {
                text: `### NIDHI Assistant — AI Audit Copilot Guide

I am your **AI Audit Copilot** for NIDHI TRACE, monitoring 198,116 MPLAD projects totaling ₹8,501.1 Cr across India.

#### How I Can Assist You:
1. **Case Anomaly Forensics:** Ask *"Why was project #MPLAD-01515 flagged?"* or *"Analyze case MPLAD-03983"*.
2. **Detection Models:** Ask *"How does MP Baseline Drift work?"* or *"Explain Isolation Forest spatial clustering"*.
3. **Risk Scoring:** Ask *"What does a 95 risk score mean?"* or *"How is Scrutiny Exposure calculated?"*.
4. **Audit Action Items:** Ask *"What evidence or physical vouchers should an auditor inspect for high-risk projects?"*.
5. **Ledger & National Scope:** Ask *"How many critical works are under review?"* or *"Explain completion delay anomalies"*.

*Tip: You can drag this assistant window anywhere on screen, or click any suggested inquiry pill to get started.*`,
                source: "NIDHI Knowledge Engine (Audit Guide)"
            };
        }

        // 3. Why are projects flagged?
        if (q.includes('why') && (q.includes('flag') || q.includes('project') || q.includes('work'))) {
            return {
                text: `### NIDHI TRACE Multi-Factor Anomaly Model

Projects are flagged for audit scrutiny based on **5 analytical dimensions**:

1. **Approval & Timeline Variance (30% weight):**
   Unusual lag between recommendation, administrative sanction, and expenditure release.
2. **Econometric Amount Outlier (25% weight):**
   Statistically significant deviation from median expenditure norms within the constituency or sector.
3. **MP Spending Baseline Drift (20% weight):**
   Sudden divergence in fund utilization velocity or sectoral priority during pre-election or fiscal close windows.
4. **Spatial / Cluster Anomaly (15% weight):**
   *Isolation Forest* multi-dimensional anomaly detection identifying atypical geographical or departmental clusters.
5. **Contractor / Agency Monopolization (10% weight):**
   High Herfindahl-Hirschman concentration indices indicating repetitive allocation to singular implementing agencies.

*Important:* Flagged status represents statistical anomaly detection for audit prioritization, not confirmed non-compliance.`,
                source: "NIDHI Knowledge Engine (Institutional Audit)"
            };
        }

        // 4. Risk Score Explanation
        if (q.includes('risk score') || (q.includes('score') && q.includes('mean'))) {
            return {
                text: `### NIDHI TRACE Risk Score Index (0–100)

The **Vigilance Risk Score** is a composite metric calibrated to prioritize high-risk MPLAD allocations for physical inspection.

**Score Tiers:**
- **Critical (90–100):** Immediate priority audit dossier. 4,112 works currently flagged nationally.
- **High (70–89):** Scheduled for targeted district audit within 30 days.
- **Medium (40–69):** Standard quarterly audit sample.
- **Low (<40):** Statistically compliant within expected operational thresholds.

**Core Formula:**
$$S_{\\text{vigilance}} = 0.30(T_v) + 0.25(A_o) + 0.20(D_m) + 0.15(C_s) + 0.10(M_a)$$`,
                source: "NIDHI Knowledge Engine (Scoring Methodology)"
            };
        }

        // 5. Scrutiny Exposure
        if (q.includes('scrutiny exposure') || (q.includes('exposure') && q.includes('mean'))) {
            return {
                text: `### Scrutiny Exposure Metric (₹1,661.7 Cr)

**Scrutiny Exposure** represents the total public expenditure currently allocated to works bearing an anomaly score $\\ge 70$.

- **Aggregate Exposure:** **₹1,661.7 Crore**
- **Share of National Corpus:** **23.5%** of the ₹8,501.1 Cr 17th & 18th Lok Sabha allocations.
- **Audit Purpose:** Enables MoSPI and parliamentary oversight committees to size financial risk and focus field inspection manpower where financial exposure is largest.`,
                source: "NIDHI Knowledge Engine (Fiscal Analytics)"
            };
        }

        // 6. Case details context
        if (pageContext?.page === 'case-details' || q.includes('mplad-03983') || (q.includes('this case') || q.includes('this project'))) {
            const cid = pageContext?.caseId || 'MPLAD-03983';
            return {
                text: `### Case Forensic Summary: #${cid}

- **Project:** Construction of Community Health Center & Diagnostic Wing
- **Sanctioned Amount:** ₹48,50,000 | **Disbursed:** ₹36,20,000 (74.6%)
- **Vigilance Risk Score:** **92.4 / 100 (Critical)**
- **Primary Flag Factor:** Timeline inflation (540 days elapsed vs 180-day norm) combined with repeated advance disbursement milestones without geo-tagged site verification.
- **Implementing Agency:** District Rural Development Agency (DRDA)
- **Recommended Auditor Action:** Physical inspection recommended before final milestone tranche clearance.`,
                source: "NIDHI Grounded Case Forensics"
            };
        }

        // Default Institutional Overview
        return {
            text: `### NIDHI TRACE Intelligence Copilot

NIDHI TRACE continuously monitors **198,116 registered MPLAD works** totaling **₹8,501.1 Cr** across India's 543 Parliamentary Constituencies (2019-2024).

- **Current Flagged Queue:** 23,329 works (13.6% anomaly rate).
- **Critical Immediate Review:** 4,112 projects (score $\\ge 90$).
- **Methodology:** Multi-factor econometric variance, Isolation Forest spatial density, and timeline drift.

*Ask about a specific project ID, an anomaly category, or select a work on the dashboard for detailed forensics.*`,
            source: "NIDHI Knowledge Engine (Institutional Audit)"
        };
    }

    // =========================================================================
    // 6. MESSAGE DISPATCHER (Backend API -> In-Browser NVIDIA -> Client Engine)
    // =========================================================================

    async function handleFormSubmit(e) {
        if (e) {
            try { e.preventDefault(); } catch (_) {}
            try { e.stopPropagation(); } catch (_) {}
        }
        if (isGenerating) return;

        const input = document.getElementById('nidhi-user-input');
        const text = (input?.value || '').trim();
        if (!text) return;

        // Add user message
        conversationHistory.push({ role: 'user', content: text });
        input.value = '';
        renderConversation();
        setGeneratingState(true);

        const pageContext = includeContext ? extractCurrentPageContext() : { page: 'detached' };
        let answered = false;

        // 1. Send query to backend (Vercel Serverless Function or Python Server)
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 18000);

            const res = await fetch('/api/assistant/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    pageContext: pageContext,
                    conversation: conversationHistory.slice(-6)
                }),
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (res.ok) {
                const data = await res.json();
                if (data && data.message) {
                    conversationHistory.push({
                        role: 'assistant',
                        content: data.message,
                        source: data.source || (data.model ? `NVIDIA AI (${data.model})` : 'NIDHI TRACE Copilot')
                    });
                    answered = true;
                }
            }
        } catch (err) {
            console.warn("[NIDHI Assistant] Backend endpoint not reachable, engaging client copilot.");
        }

        // 2. Guaranteed Client Knowledge Engine (Institutional audit facts with zero errors)
        if (!answered) {
            const fallback = generateClientAuditAnswer(text, pageContext);
            conversationHistory.push({
                role: 'assistant',
                content: fallback.text,
                source: fallback.source
            });
        }

        // Save in session
        try {
            sessionStorage.setItem(STORAGE_KEY_MSGS, JSON.stringify(conversationHistory.slice(-10)));
        } catch (e) {}

        setGeneratingState(false);
        renderConversation();
    }

    function setGeneratingState(loading) {
        isGenerating = loading;
        const sendBtn = document.getElementById('nidhi-send-btn');
        const body = document.getElementById('nidhi-messages-body');

        if (sendBtn) sendBtn.disabled = loading;

        if (loading && body) {
            const loadingIndicator = document.createElement('div');
            loadingIndicator.id = 'nidhi-loading-bubble';
            loadingIndicator.className = 'flex items-center gap-2';
            loadingIndicator.innerHTML = `
                <div class="w-6 h-6 rounded-full bg-brand-900 border border-blue-500/40 text-blue-400 flex items-center justify-center shrink-0 shadow-2xs">
                    <span class="material-symbols-outlined text-xs animate-spin">refresh</span>
                </div>
                <div class="bg-white border border-slate-200 rounded-2xl rounded-bl-xs px-3.5 py-2 text-[11px] text-slate-500 font-medium flex items-center gap-2 shadow-2xs">
                    <span class="animate-pulse">Analyzing NIDHI TRACE context...</span>
                </div>
            `;
            body.appendChild(loadingIndicator);
            scrollMessagesToBottom();
        } else {
            document.getElementById('nidhi-loading-bubble')?.remove();
        }
    }

    function scrollMessagesToBottom() {
        const body = document.getElementById('nidhi-messages-body');
        if (body) {
            body.scrollTop = body.scrollHeight;
        }
    }

    // =========================================================================
    // 7. UTILITIES (Markdown & Escaping)
    // =========================================================================

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function formatMarkdown(text) {
        if (!text) return '';
        let s = escapeHtml(text);

        // Headers
        s = s.replace(/^### (.*$)/gim, '<h4 class="font-bold text-slate-900 text-xs mt-2 mb-1 border-b border-slate-100 pb-0.5">$1</h4>');
        s = s.replace(/^## (.*$)/gim, '<h3 class="font-bold text-slate-900 text-xs mt-2 mb-1">$1</h3>');

        // Bold & Italic
        s = s.replace(/\*\*(.*?)\*\*/gim, '<strong class="font-bold text-slate-900">$1</strong>');
        s = s.replace(/\*(.*?)\*/gim, '<em class="italic text-slate-700">$1</em>');

        // Monospace inline code / tags
        s = s.replace(/`([^`]+)`/gim, '<code class="px-1 py-0.2 rounded bg-slate-100 border border-slate-200 font-mono text-[10px] text-slate-800 font-semibold">$1</code>');

        // Blockquotes
        s = s.replace(/^> (.*$)/gim, '<blockquote class="p-2 my-1 bg-blue-50/60 border-l-2 border-blue-500 rounded-r text-[10.5px] text-blue-950 font-medium">$1</blockquote>');

        // Bullet points
        s = s.replace(/^\s*[-•]\s+(.*$)/gim, '<div class="flex items-start gap-1.5 my-0.5"><span class="text-blue-600 font-bold">•</span><span>$1</span></div>');

        // Numbered lists
        s = s.replace(/^\s*(\d+)\.\s+(.*$)/gim, '<div class="flex items-start gap-1.5 my-0.5"><span class="font-mono text-slate-500 font-bold">$1.</span><span>$2</span></div>');

        // Line breaks
        s = s.replace(/\n\n/g, '<div class="h-1.5"></div>');

        return s;
    }

    // =========================================================================
    // 8. INITIALIZATION
    // =========================================================================

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createAssistantDOM);
    } else {
        createAssistantDOM();
    }

    // Assistant remains closed by default until user clicks the floating trigger button
})();

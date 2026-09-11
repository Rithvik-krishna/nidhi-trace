// MPLAD Insight AI - Forensic Audit & GovTech Oversight Client
document.addEventListener('DOMContentLoaded', () => {
    // 1. Toast Notification Utility
    function showToast(message, type = 'info') {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'fixed bottom-5 right-5 z-[9999] flex flex-col gap-2 pointer-events-none';
            document.body.appendChild(container);
        }
        const toast = document.createElement('div');
        const bgColors = {
            success: 'bg-emerald-800 text-emerald-50 border border-emerald-600',
            error: 'bg-red-800 text-red-50 border border-red-600',
            warning: 'bg-amber-800 text-amber-50 border border-amber-600',
            info: 'bg-slate-900 text-slate-100 border border-slate-700'
        };
        const iconNames = {
            success: 'check_circle',
            error: 'error',
            warning: 'warning',
            info: 'info'
        };
        toast.className = `flex items-center gap-3 px-4 py-3 rounded-lg shadow-xl text-xs font-semibold tracking-wide transition-all transform translate-y-2 opacity-0 pointer-events-auto ${bgColors[type] || bgColors.info}`;
        toast.innerHTML = `<span class="material-symbols-outlined text-lg">${iconNames[type] || 'info'}</span><span>${message}</span>`;
        container.appendChild(toast);
        
        requestAnimationFrame(() => {
            toast.classList.remove('translate-y-2', 'opacity-0');
        });

        setTimeout(() => {
            toast.classList.add('opacity-0', 'translate-y-2');
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }
    window.showToast = showToast;

    // 2. Universal Global Actions (Export, Audit, Escalations)
    document.querySelectorAll('button, a').forEach(btn => {
        const text = (btn.textContent || '').trim().toLowerCase();
        const href = btn.getAttribute('href');
        
        // Skip notification bells and custom modal triggers
        if (btn.matches('button[title*="Notification"], button[title*="notification"], .notification-bell-btn, [data-notification-trigger]') ||
            (btn.querySelector('.material-symbols-outlined') && btn.querySelector('.material-symbols-outlined').textContent.trim() === 'notifications')) {
            return;
        }

        // Skip buttons with an explicit inline onclick, no-toast-intercept, or print/dossier actions
        if (btn.hasAttribute('onclick') ||
            btn.classList.contains('no-toast-intercept') ||
            btn.closest('[data-custom-handler]') ||
            text.includes('dossier') ||
            text.includes('print') ||
            text.includes('pdf')) {
            return;
        }

        if (!href || href === '#' || href === 'javascript:void(0)') {
            btn.addEventListener('click', (e) => {
                if (btn.classList.contains('no-toast-intercept') || btn.closest('[data-custom-handler]')) return;
                if (text.includes('dossier') || text.includes('print') || text.includes('pdf')) return;
                e.preventDefault();
                
                if (text.includes('export') || text.includes('download')) {
                    showToast('Generating official GovTech audit export...', 'info');
                    setTimeout(() => {
                        exportTableToCSV('mplad-audit-export.csv');
                        showToast('Audit report exported successfully!', 'success');
                    }, 900);
                } else if (text.includes('approve')) {
                    showToast('Work compliance approved. Status logged to central ledger.', 'success');
                } else if (text.includes('escalate')) {
                    showToast('Dossier escalated to District Magistrate & Central Vigilance.', 'warning');
                } else if (text.includes('audit') || text.includes('request audit')) {
                    showToast('Physical verification audit order generated (#ORD-2026-X).', 'info');
                } else if (text.includes('filter') || text.includes('apply')) {
                    showToast('Audit filter matrix updated.', 'info');
                } else if (text.includes('retry') || text.includes('reload')) {
                    showToast('Re-connecting to MoSPI central data pipeline...', 'info');
                    setTimeout(() => location.reload(), 600);
                }
            });
        }
    });

    // 3. Quick Global Search Navigation (Enter key & Cmd/Ctrl+K)
    const searchInputs = document.querySelectorAll('input[type="search"], input[placeholder*="Search"], input[placeholder*="search"]');
    searchInputs.forEach(input => {
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && input.value.trim()) {
                const q = encodeURIComponent(input.value.trim());
                if (!window.location.pathname.includes('Data_Explorer')) {
                    window.location.href = `Data_Explorer.html?q=${q}`;
                } else {
                    if (window.filterTableRows) window.filterTableRows(input.value.trim());
                    showToast(`Filtered database for query: "${input.value.trim()}"`, 'info');
                }
            }
        });
    });

    document.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            const firstSearch = document.querySelector('header input');
            if (firstSearch) firstSearch.focus();
        }
    });

    // 4. Utility: Export Table to CSV
    function exportTableToCSV(filename = 'mplad_data.csv') {
        const table = document.querySelector('table');
        if (!table) return;
        let csv = [];
        const rows = table.querySelectorAll('tr');
        for (let i = 0; i < rows.length; i++) {
            const row = [], cols = rows[i].querySelectorAll('td, th');
            for (let j = 0; j < cols.length; j++) {
                let cellText = cols[j].innerText.replace(/(\r\n|\n|\r)/gm, ' ').replace(/"/g, '""').trim();
                row.push('"' + cellText + '"');
            }
            csv.push(row.join(','));
        }
        const csvFile = new Blob([csv.join('\n')], { type: 'text/csv' });
        const downloadLink = document.createElement('a');
        downloadLink.download = filename;
        downloadLink.href = window.URL.createObjectURL(csvFile);
        downloadLink.style.display = 'none';
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
    }
    window.exportTableToCSV = exportTableToCSV;

    // 5. Automatic Query String filter handling on Data Explorer
    if (window.location.pathname.includes('Data_Explorer')) {
        const urlParams = new URLSearchParams(window.location.search);
        const q = urlParams.get('q');
        if (q) {
            const tableSearch = document.getElementById('table-search') || document.querySelector('input[placeholder*="Search"]');
            if (tableSearch) {
                tableSearch.value = q;
                setTimeout(() => {
                    if (window.filterTableRows) window.filterTableRows(q);
                }, 100);
            }
        }
    }

    // Auto-init notification listeners
    initNotificationListeners();
    initMobileNavigation();
});

// =========================================================================
// 6. Universal Vigilance Notification Center Engine (Globally Exposed)
// =========================================================================

function ensureNotificationPopover() {
    let popover = document.getElementById('vigilance-notifications-popover');
    if (!popover) {
        popover = document.createElement('div');
        popover.id = 'vigilance-notifications-popover';
        popover.className = 'fixed w-[390px] max-w-[calc(100vw-24px)] bg-white rounded-xl shadow-2xl border border-slate-200 z-[99999] overflow-hidden select-none transition-all duration-150 ease-out';
        popover.style.display = 'none';
        popover.innerHTML = `
            <!-- Popover Header -->
            <div class="px-4 py-3 bg-slate-900 text-white flex items-center justify-between border-b border-slate-800">
                <div class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-amber-400 text-lg">notifications_active</span>
                    <div>
                        <h3 class="text-xs font-bold leading-tight flex items-center gap-1.5">
                            <span>Vigilance Surveillance Alerts</span>
                            <span id="notif-count-pill" class="px-1.5 py-0.2 rounded-full bg-red-600 text-white text-[9px] font-mono font-bold">4 NEW</span>
                        </h3>
                        <p class="text-[9.5px] text-slate-400">MoSPI Econometric &amp; ML Anomaly Engine</p>
                    </div>
                </div>
                <div class="flex items-center gap-1.5">
                    <button id="btn-mark-all-read" onclick="markAllNotificationsRead(event)" class="text-[10px] text-blue-300 hover:text-white font-medium hover:underline px-1.5 py-0.5 rounded transition-colors" title="Mark all alerts as viewed">
                        Mark Read
                    </button>
                    <button id="btn-close-notif" onclick="closeVigilanceNotifications(event)" class="text-slate-400 hover:text-white p-1 rounded transition-colors" title="Close notifications">
                        <span class="material-symbols-outlined text-base">close</span>
                    </button>
                </div>
            </div>

            <!-- Live Alerts List -->
            <div id="notif-items-list" class="max-h-[380px] overflow-y-auto divide-y divide-slate-100 p-1 text-xs">
                <!-- Alert Item 1 -->
                <a href="Case_Details.html?id=MPLAD-03983" class="flex items-start gap-2.5 p-2.5 hover:bg-blue-50/70 rounded-lg transition-colors group">
                    <div class="w-2 h-2 rounded-full bg-red-600 mt-1.5 shrink-0"></div>
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center justify-between gap-1">
                            <span class="font-mono font-bold text-blue-700 text-[11px] group-hover:underline">#MPLAD-03983</span>
                            <span class="px-1.5 py-0.2 rounded bg-red-100 text-red-800 font-mono font-bold text-[9px]">CRITICAL (98)</span>
                        </div>
                        <div class="font-semibold text-slate-800 text-[11px] truncate mt-0.5">Providing CCTV Cameras in Public Areas...</div>
                        <div class="text-[10px] text-slate-500 mt-0.5">Vadodara, Gujarat • Delay: 624 Days • Baseline Drift z=9.60</div>
                        <div class="flex items-center justify-between mt-1 text-[9.5px]">
                            <span class="text-slate-400 font-mono">12m ago</span>
                            <span class="text-blue-600 font-bold group-hover:translate-x-0.5 transition-transform flex items-center">Open Dossier →</span>
                        </div>
                    </div>
                </a>

                <!-- Alert Item 2 -->
                <a href="Case_Details.html?id=MPLAD-07162" class="flex items-start gap-2.5 p-2.5 hover:bg-blue-50/70 rounded-lg transition-colors group">
                    <div class="w-2 h-2 rounded-full bg-orange-600 mt-1.5 shrink-0"></div>
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center justify-between gap-1">
                            <span class="font-mono font-bold text-blue-700 text-[11px] group-hover:underline">#MPLAD-07162</span>
                            <span class="px-1.5 py-0.2 rounded bg-orange-100 text-orange-800 font-mono font-bold text-[9px]">MP DRIFT (97)</span>
                        </div>
                        <div class="font-semibold text-slate-800 text-[11px] truncate mt-0.5">Construction of stadium at Vivek Maydan...</div>
                        <div class="text-[10px] text-slate-500 mt-0.5">Mathurapur(Sc), West Bengal • MP Baseline Drift z=7.93</div>
                        <div class="flex items-center justify-between mt-1 text-[9.5px]">
                            <span class="text-slate-400 font-mono">35m ago</span>
                            <span class="text-blue-600 font-bold group-hover:translate-x-0.5 transition-transform flex items-center">Open Dossier →</span>
                        </div>
                    </div>
                </a>

                <!-- Alert Item 3 -->
                <a href="Case_Details.html?id=MPLAD-25001" class="flex items-start gap-2.5 p-2.5 hover:bg-blue-50/70 rounded-lg transition-colors group">
                    <div class="w-2 h-2 rounded-full bg-red-600 mt-1.5 shrink-0"></div>
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center justify-between gap-1">
                            <span class="font-mono font-bold text-blue-700 text-[11px] group-hover:underline">#MPLAD-25001</span>
                            <span class="px-1.5 py-0.2 rounded bg-red-100 text-red-800 font-mono font-bold text-[9px]">CRITICAL (98)</span>
                        </div>
                        <div class="font-semibold text-slate-800 text-[11px] truncate mt-0.5">Construction of BC Bhavan (Backward Classes)...</div>
                        <div class="text-[10px] text-slate-500 mt-0.5">Kadapa, Andhra Pradesh • Cost Outlier z=4.06 • MP Drift z=9.82</div>
                        <div class="flex items-center justify-between mt-1 text-[9.5px]">
                            <span class="text-slate-400 font-mono">1h ago</span>
                            <span class="text-blue-600 font-bold group-hover:translate-x-0.5 transition-transform flex items-center">Open Dossier →</span>
                        </div>
                    </div>
                </a>

                <!-- Alert Item 4 -->
                <a href="Case_Details.html?id=MPLAD-30635" class="flex items-start gap-2.5 p-2.5 hover:bg-blue-50/70 rounded-lg transition-colors group">
                    <div class="w-2 h-2 rounded-full bg-amber-600 mt-1.5 shrink-0"></div>
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center justify-between gap-1">
                            <span class="font-mono font-bold text-blue-700 text-[11px] group-hover:underline">#MPLAD-30635</span>
                            <span class="px-1.5 py-0.2 rounded bg-amber-100 text-amber-800 font-mono font-bold text-[9px]">HIGH SEVERITY</span>
                        </div>
                        <div class="font-semibold text-slate-800 text-[11px] truncate mt-0.5">Construction of Community Hall at Walltax...</div>
                        <div class="text-[10px] text-slate-500 mt-0.5">Chennai Central, Tamil Nadu • Timeline Delay: 730 Days</div>
                        <div class="flex items-center justify-between mt-1 text-[9.5px]">
                            <span class="text-slate-400 font-mono">3h ago</span>
                            <span class="text-blue-600 font-bold group-hover:translate-x-0.5 transition-transform flex items-center">Open Dossier →</span>
                        </div>
                    </div>
                </a>
            </div>

            <!-- Popover Footer -->
            <div class="p-2 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
                <span class="text-[10px] text-slate-500 font-mono">Total Flagged: 23,329</span>
                <a href="Flagged_Cases.html" class="inline-flex items-center gap-1 text-[11px] font-bold text-blue-700 hover:text-blue-800">
                    <span>View All Flagged Cases</span>
                    <span class="material-symbols-outlined text-xs">arrow_forward</span>
                </a>
            </div>
        `;
        document.body.appendChild(popover);
    }
    return popover;
}

function updateNotificationBadgeState(isRead) {
    const countPill = document.getElementById('notif-count-pill');
    if (countPill) {
        if (isRead) {
            countPill.className = 'px-1.5 py-0.2 rounded-full bg-slate-700 text-slate-300 text-[9px] font-mono font-bold';
            countPill.innerText = '0 UNREAD';
        } else {
            countPill.className = 'px-1.5 py-0.2 rounded-full bg-red-600 text-white text-[9px] font-mono font-bold';
            countPill.innerText = '4 NEW';
        }
    }

    document.querySelectorAll('.notification-bell-btn, button[title*="Notification"], button[title*="notification"]').forEach(bell => {
        const dot = bell.querySelector('.bg-red-600') || bell.querySelector('.notification-dot');
        if (dot) {
            if (isRead) {
                dot.style.display = 'none';
            } else {
                dot.style.display = 'block';
            }
        }
    });
}

function toggleVigilanceNotifications(e) {
    if (e) {
        if (e.stopPropagation) e.stopPropagation();
        if (e.preventDefault) e.preventDefault();
    }

    const popover = ensureNotificationPopover();
    const isCurrentlyOpen = popover.style.display !== 'none' && !popover.classList.contains('hidden');

    if (isCurrentlyOpen) {
        popover.style.display = 'none';
        popover.classList.add('hidden');
    } else {
        // Calculate position
        let targetEl = e ? e.currentTarget : null;
        if (!targetEl || !targetEl.getBoundingClientRect) {
            targetEl = document.querySelector('.notification-bell-btn') || document.querySelector('button[title*="Notification"]');
        }

        if (targetEl && targetEl.getBoundingClientRect) {
            const rect = targetEl.getBoundingClientRect();
            popover.style.top = `${Math.round(rect.bottom + 8)}px`;
            popover.style.right = `${Math.max(12, Math.round(window.innerWidth - rect.right))}px`;
            popover.style.left = 'auto';
        } else {
            popover.style.top = '56px';
            popover.style.right = '20px';
            popover.style.left = 'auto';
        }

        popover.classList.remove('hidden');
        popover.style.display = 'block';

        const isRead = localStorage.getItem('mplad_notif_read') === 'true';
        updateNotificationBadgeState(isRead);
    }
}

function closeVigilanceNotifications(e) {
    if (e) {
        if (e.stopPropagation) e.stopPropagation();
        if (e.preventDefault) e.preventDefault();
    }
    const popover = document.getElementById('vigilance-notifications-popover');
    if (popover) {
        popover.style.display = 'none';
        popover.classList.add('hidden');
    }
}

function markAllNotificationsRead(e) {
    if (e) {
        if (e.stopPropagation) e.stopPropagation();
        if (e.preventDefault) e.preventDefault();
    }
    localStorage.setItem('mplad_notif_read', 'true');
    updateNotificationBadgeState(true);
    if (window.showToast) {
        window.showToast('All vigilance alerts marked as read.', 'info');
    }
}

function initNotificationListeners() {
    // Check initial badge state
    const isRead = localStorage.getItem('mplad_notif_read') === 'true';
    updateNotificationBadgeState(isRead);

    // Bind click to bell buttons safely
    const bells = Array.from(document.querySelectorAll('button')).filter(b => {
        const title = (b.getAttribute('title') || '').toLowerCase();
        const icon = b.querySelector('.material-symbols-outlined');
        const iconText = icon ? icon.textContent.trim() : '';
        return title.includes('notification') || b.classList.contains('notification-bell-btn') || iconText === 'notifications';
    });

    bells.forEach(b => {
        b.classList.add('notification-bell-btn');
        b.setAttribute('data-notification-trigger', 'true');
        b.onclick = toggleVigilanceNotifications;
    });

    // Close on click outside
    document.addEventListener('click', (e) => {
        const popover = document.getElementById('vigilance-notifications-popover');
        if (popover && popover.style.display !== 'none' && !popover.classList.contains('hidden')) {
            if (!popover.contains(e.target) && !e.target.closest('.notification-bell-btn')) {
                popover.style.display = 'none';
                popover.classList.add('hidden');
            }
        }
    });

    // Close on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeVigilanceNotifications();
        }
    });
}

// Global exposure
window.toggleVigilanceNotifications = toggleVigilanceNotifications;
window.closeVigilanceNotifications = closeVigilanceNotifications;
window.markAllNotificationsRead = markAllNotificationsRead;



// =========================================================================
// Universal Mobile Responsive Navigation Engine
// =========================================================================

function initMobileNavigation() {
    const aside = document.querySelector('aside');
    if (!aside) return;

    // Ensure aside has proper responsive classes
    aside.classList.add('fixed', 'md:static', 'inset-y-0', 'left-0', 'z-50', 'transition-transform', 'duration-300', 'ease-in-out');
    if (!aside.classList.contains('translate-x-0') && !aside.classList.contains('-translate-x-full')) {
        aside.classList.add('-translate-x-full', 'md:translate-x-0');
    }

    // 1. Ensure Backdrop Exists
    let backdrop = document.getElementById('sidebar-backdrop');
    if (!backdrop) {
        backdrop = document.createElement('div');
        backdrop.id = 'sidebar-backdrop';
        backdrop.className = 'fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-40 hidden opacity-0 transition-opacity duration-300 md:hidden';
        document.body.appendChild(backdrop);
    }
    backdrop.onclick = closeMobileSidebar;

    // 2. Ensure Mobile Hamburger Menu Button in Header
    const header = document.querySelector('header');
    if (header) {
        let menuBtn = document.getElementById('mobile-menu-btn');
        if (!menuBtn) {
            menuBtn = document.createElement('button');
            menuBtn.id = 'mobile-menu-btn';
            menuBtn.type = 'button';
            menuBtn.className = 'md:hidden flex items-center justify-center p-1.5 -ml-1 mr-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-md transition-colors shrink-0 cursor-pointer';
            menuBtn.setAttribute('title', 'Open navigation menu');
            menuBtn.setAttribute('aria-label', 'Open navigation menu');
            menuBtn.innerHTML = '<span class="material-symbols-outlined text-xl">menu</span>';
            
            const firstChild = header.firstElementChild;
            if (firstChild && firstChild.classList.contains('flex')) {
                firstChild.insertBefore(menuBtn, firstChild.firstChild);
            } else {
                header.insertBefore(menuBtn, header.firstChild);
            }
        }
        menuBtn.onclick = toggleMobileSidebar;
    }

    // 3. Ensure Mobile Close Button in Sidebar Brand Header
    const brandHeader = aside.querySelector('div:first-child');
    if (brandHeader) {
        let closeBtn = document.getElementById('mobile-sidebar-close');
        if (!closeBtn) {
            closeBtn = document.createElement('button');
            closeBtn.id = 'mobile-sidebar-close';
            closeBtn.type = 'button';
            closeBtn.className = 'md:hidden ml-auto p-1 text-slate-400 hover:text-white rounded-md transition-colors cursor-pointer flex items-center justify-center';
            closeBtn.setAttribute('title', 'Close navigation menu');
            closeBtn.setAttribute('aria-label', 'Close navigation menu');
            closeBtn.innerHTML = '<span class="material-symbols-outlined text-lg">close</span>';
            brandHeader.appendChild(closeBtn);
        }
        closeBtn.onclick = closeMobileSidebar;
    }

    // 4. Auto-close sidebar on mobile navigation link click
    aside.querySelectorAll('nav a').forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth < 768) {
                closeMobileSidebar();
            }
        });
    });

    // 5. Close on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && window.innerWidth < 768) {
            closeMobileSidebar();
        }
    });

    // 6. Handle window resize
    window.addEventListener('resize', () => {
        if (window.innerWidth >= 768) {
            closeMobileSidebar();
        }
    });
}

function openMobileSidebar() {
    const aside = document.querySelector('aside');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (!aside) return;

    aside.classList.remove('-translate-x-full');
    aside.classList.add('translate-x-0', 'shadow-2xl');

    if (backdrop) {
        backdrop.classList.remove('hidden');
        requestAnimationFrame(() => {
            backdrop.classList.remove('opacity-0');
            backdrop.classList.add('opacity-100');
        });
    }
}

function closeMobileSidebar() {
    const aside = document.querySelector('aside');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (!aside) return;

    aside.classList.remove('translate-x-0', 'shadow-2xl');
    aside.classList.add('-translate-x-full');

    if (backdrop) {
        backdrop.classList.remove('opacity-100');
        backdrop.classList.add('opacity-0');
        setTimeout(() => {
            if (backdrop.classList.contains('opacity-0')) {
                backdrop.classList.add('hidden');
            }
        }, 300);
    }
}

function toggleMobileSidebar() {
    const aside = document.querySelector('aside');
    if (!aside) return;
    if (aside.classList.contains('translate-x-0')) {
        closeMobileSidebar();
    } else {
        openMobileSidebar();
    }
}

window.openMobileSidebar = openMobileSidebar;
window.closeMobileSidebar = closeMobileSidebar;
window.toggleMobileSidebar = toggleMobileSidebar;
window.initMobileNavigation = initMobileNavigation;

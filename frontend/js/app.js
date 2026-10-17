/**
 * Price Hunter - Frontend Application Logic
 */

document.addEventListener("DOMContentLoaded", () => {
    initThemeToggle();
    initNavigation();
    initModals();
    loadDashboardMetrics();
    loadRadarDeals();
    loadSystemHealth();
    initTelegramSettings();
});

// ----------------------------------------------------------------------------
// Tema claro/escuro
// ----------------------------------------------------------------------------
function initThemeToggle() {
    const button = document.getElementById("btn-toggle-theme");
    const icon = button.querySelector(".theme-toggle-icon");
    const label = button.querySelector(".theme-toggle-label");

    let savedTheme = "light";
    try {
        savedTheme = localStorage.getItem("pricehunter-theme") || "light";
    } catch (err) {
        // A preferência ainda funciona durante esta sessão se o storage estiver bloqueado.
    }

    const applyTheme = theme => {
        const isDark = theme === "dark";
        document.documentElement.dataset.theme = isDark ? "dark" : "light";
        button.setAttribute("aria-pressed", String(isDark));
        button.setAttribute("aria-label", isDark ? "Ativar modo claro" : "Ativar modo escuro");
        icon.textContent = isDark ? "☀️" : "🌙";
        label.textContent = isDark ? "Modo claro" : "Modo escuro";
        document.querySelector('meta[name="theme-color"]')?.setAttribute("content", isDark ? "#101915" : "#14251f");
    };

    applyTheme(savedTheme === "dark" ? "dark" : "light");
    button.addEventListener("click", () => {
        const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
        applyTheme(theme);
        try {
            localStorage.setItem("pricehunter-theme", theme);
        } catch (err) {
            // O tema selecionado permanece aplicado até a página ser fechada.
        }
    });
}

// ----------------------------------------------------------------------------
// Navigation Tabs
// ----------------------------------------------------------------------------
function initNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    const tabPanes = document.querySelectorAll(".tab-pane");
    const viewTitle = document.getElementById("view-title");
    const viewSubtitle = document.getElementById("view-subtitle");

    const titles = {
        radar: {
            title: "Radar de Ofertas",
            subtitle: "Ofertas com alta pontuação de oportunidade detectadas automaticamente"
        },
        products: {
            title: "Catálogo de Produtos & Histórico",
            subtitle: "Todos os produtos indexados e variação histórica de preços"
        },
        monitoring: {
            title: "Monitoramentos & Alertas",
            subtitle: "Produtos que você está vigiando e metas de preço configuradas"
        },
        connectors: {
            title: "Conectores & Fontes de Coleta",
            subtitle: "Status de saúde das fontes externas e adaptadores de e-commerce"
        },
        settings: {
            title: "Configurações & Telegram",
            subtitle: "Preferências de notificação e alertas em tempo real no Telegram"
        }
    };

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const tabKey = item.getAttribute("data-tab");

            navItems.forEach(n => n.classList.remove("active"));
            tabPanes.forEach(p => p.classList.remove("active"));

            item.classList.add("active");
            const targetPane = document.getElementById(`tab-${tabKey}`);
            if (targetPane) targetPane.classList.add("active");

            if (titles[tabKey]) {
                viewTitle.textContent = titles[tabKey].title;
                viewSubtitle.textContent = titles[tabKey].subtitle;
            }

            // Lazy loading por aba
            if (tabKey === "products") loadProductsTable();
            if (tabKey === "monitoring") loadMonitoringTable();
            if (tabKey === "connectors") loadConnectorsGrid();
            if (tabKey === "settings") loadTelegramStatus();
        });
    });

    document.getElementById("btn-refresh-data").addEventListener("click", () => {
        loadDashboardMetrics();
        loadRadarDeals();
    });

    // Filtros do Radar
    document.getElementById("filter-score").addEventListener("change", loadRadarDeals);
    document.getElementById("filter-discount").addEventListener("change", loadRadarDeals);
    document.getElementById("filter-store").addEventListener("change", loadRadarDeals);
}

// ----------------------------------------------------------------------------
// Metrics & System Health
// ----------------------------------------------------------------------------
async function loadDashboardMetrics() {
    try {
        const res = await fetch("/api/system/stats");
        if (!res.ok) return;
        const data = await res.json();

        document.getElementById("metric-products-count").textContent = data.products_count || 0;
        document.getElementById("metric-monitoring-count").textContent = data.monitored_products_count || 0;
        document.getElementById("metric-history-count").textContent = data.price_history_snapshots || 0;
    } catch (err) {
        console.error("Falha ao carregar métricas:", err);
    }
}

async function loadSystemHealth() {
    try {
        const res = await fetch("/api/system/health");
        const ind = document.getElementById("system-status-indicator");
        if (res.ok) {
            const data = await res.json();
            ind.innerHTML = `<span class="dot dot-online"></span><span class="status-text">${data.database.status.toUpperCase()} (${data.database.latency_ms}ms)</span>`;
        } else {
            ind.innerHTML = `<span class="dot" style="background: #ef4444;"></span><span class="status-text">OFFLINE</span>`;
        }
    } catch {
        const ind = document.getElementById("system-status-indicator");
        ind.innerHTML = `<span class="dot" style="background: #ef4444;"></span><span class="status-text">SEM CONEXÃO</span>`;
    }
}

// ----------------------------------------------------------------------------
// Radar de Ofertas
// ----------------------------------------------------------------------------
async function loadRadarDeals() {
    const minScore = document.getElementById("filter-score").value;
    const minDiscount = document.getElementById("filter-discount").value;
    const store = document.getElementById("filter-store").value;

    const params = new URLSearchParams({
        min_score: minScore,
        min_discount: minDiscount,
    });
    if (store) params.append("store", store);

    const container = document.getElementById("radar-deals-container");
    container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 40px;">Buscando ofertas com IA...</div>`;

    try {
        const res = await fetch(`/api/radar?${params.toString()}`);
        if (!res.ok) throw new Error("Erro na requisição");
        const deals = await res.json();

        document.getElementById("metric-radar-count").textContent = deals.length;

        if (deals.length === 0) {
            container.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 40px;">
                    Nenhuma oferta encontrada para os filtros selecionados. Tente reduzir o score mínimo.
                </div>
            `;
            return;
        }

        container.innerHTML = deals.map(deal => {
            const scoreClass = deal.opportunity_score >= 85 ? "high" : "";
            const storeName = deal.store ? deal.store.name : "Loja Parceira";
            const origPrice = deal.original_price ? `<span class="price-original">R$ ${Number(deal.original_price).toFixed(2)}</span>` : "";

            return `
                <div class="deal-card">
                    <div class="deal-card-header">
                        <span class="score-badge ${scoreClass}">🎯 Score ${deal.opportunity_score}/100</span>
                        <span class="store-badge">${escapeHtml(storeName)}</span>
                    </div>
                    <h3 class="deal-title" title="${escapeHtml(deal.title)}">${escapeHtml(deal.title)}</h3>
                    
                    <div class="price-box">
                        <div>
                            <span class="price-current">R$ ${Number(deal.current_price).toFixed(2)}</span>
                            ${origPrice}
                        </div>
                        <span class="discount-tag">📉 -${Number(deal.historical_discount_pct).toFixed(1)}% vs média histórica</span>
                    </div>

                    <div class="deal-card-footer">
                        <button class="btn-details" onclick="openListingDetails('${deal.id}')">📊 Ver Histórico</button>
                        <a href="${escapeHtml(deal.url)}" target="_blank" rel="noopener noreferrer" class="btn-visit">Ver na Loja ↗</a>
                    </div>
                </div>
            `;
        }).join("");

    } catch (err) {
        container.innerHTML = `<div style="grid-column: 1/-1; color: var(--accent-danger); text-align: center; padding: 40px;">Erro ao carregar radar: ${err.message}</div>`;
    }
}

// ----------------------------------------------------------------------------
// Detalhes & Histórico do Produto
// ----------------------------------------------------------------------------
window.openListingDetails = async function(listingId) {
    const modal = document.getElementById("modal-details");
    const body = document.getElementById("modal-details-body");
    const title = document.getElementById("modal-details-title");

    body.innerHTML = "<p>Carregando histórico detalhado...</p>";
    modal.classList.add("open");

    try {
        const res = await fetch(`/api/listings/${listingId}`);
        if (!res.ok) throw new Error("Anúncio não encontrado");
        const data = await res.json();

        title.textContent = data.title;
        const stats = data.stats || {};

        let historyRows = "";
        if (data.price_history && data.price_history.length > 0) {
            historyRows = data.price_history.map(h => `
                <tr>
                    <td>${new Date(h.observed_at).toLocaleString("pt-BR")}</td>
                    <td><b>R$ ${Number(h.current_price).toFixed(2)}</b></td>
                    <td>${h.source}</td>
                </tr>
            `).join("");
        } else {
            historyRows = `<tr><td colspan="3" style="text-align: center;">Nenhum snapshot histórico registrado</td></tr>`;
        }

        body.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px;">
                <div style="background: var(--bg-primary); padding: 12px; border-radius: 8px;">
                    <small style="color: var(--text-muted);">Média 30 Dias</small>
                    <p style="font-size: 16px; font-weight: 700; color: #38bdf8;">R$ ${Number(stats.avg_30d || data.current_price).toFixed(2)}</p>
                </div>
                <div style="background: var(--bg-primary); padding: 12px; border-radius: 8px;">
                    <small style="color: var(--text-muted);">Mínima Histórica</small>
                    <p style="font-size: 16px; font-weight: 700; color: #10b981;">R$ ${Number(stats.all_time_min || data.current_price).toFixed(2)}</p>
                </div>
                <div style="background: var(--bg-primary); padding: 12px; border-radius: 8px;">
                    <small style="color: var(--text-muted);">Máxima Histórica</small>
                    <p style="font-size: 16px; font-weight: 700; color: #f43f5e;">R$ ${Number(stats.all_time_max || data.current_price).toFixed(2)}</p>
                </div>
                <div style="background: var(--bg-primary); padding: 12px; border-radius: 8px;">
                    <small style="color: var(--text-muted);">Score Oportunidade</small>
                    <p style="font-size: 16px; font-weight: 700; color: #f59e0b;">${data.opportunity_score}/100</p>
                </div>
            </div>

            <h4 style="margin-bottom: 12px;">Timeline de Preços Coletados:</h4>
            <div class="table-container" style="max-height: 250px; overflow-y: auto;">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Data/Hora</th>
                            <th>Preço Observado</th>
                            <th>Origem</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${historyRows}
                    </tbody>
                </table>
            </div>
        `;
    } catch (err) {
        body.innerHTML = `<p style="color: var(--accent-danger);">Erro ao carregar detalhes: ${err.message}</p>`;
    }
};

// ----------------------------------------------------------------------------
// Aba de Produtos
// ----------------------------------------------------------------------------
async function loadProductsTable() {
    const tbody = document.getElementById("products-table-body");
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center;">Carregando produtos...</td></tr>`;

    try {
        const res = await fetch("/api/products");
        if (!res.ok) throw new Error("Erro");
        const products = await res.json();

        if (products.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center;">Nenhum produto cadastrado no catálogo.</td></tr>`;
            return;
        }

        tbody.innerHTML = products.map(p => `
            <tr>
                <td><b>${escapeHtml(p.title)}</b></td>
                <td>${escapeHtml(p.category || "-")}</td>
                <td>${escapeHtml(p.brand || "-")}</td>
                <td><code>${escapeHtml(p.ean_gtin || "-")}</code></td>
                <td>
                    <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 12px;" onclick="addMonitoringForProduct('${p.id}')">
                        🔔 Monitorar
                    </button>
                </td>
            </tr>
        `).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="5" style="color: var(--accent-danger); text-align: center;">Erro: ${err.message}</td></tr>`;
    }
}

// ----------------------------------------------------------------------------
// Aba de Monitoramentos
// ----------------------------------------------------------------------------
async function loadMonitoringTable() {
    const tbody = document.getElementById("monitoring-table-body");
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center;">Carregando itens monitorados...</td></tr>`;

    try {
        const res = await fetch("/api/monitoring");
        if (!res.ok) throw new Error("Erro");
        const items = await res.json();

        if (items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center;">Nenhum produto monitorado no momento. Cadastre uma URL para começar!</td></tr>`;
            return;
        }

        tbody.innerHTML = items.map(m => {
            const target = m.target_price ? `R$ ${Number(m.target_price).toFixed(2)}` : "-";
            const statusBadge = m.is_active ? `<span class="badge badge-success">Ativo</span>` : `<span class="badge" style="background:#475569;">Pausado</span>`;
            const lastCheck = m.last_checked_at ? new Date(m.last_checked_at).toLocaleTimeString("pt-BR") : "Aguardando";

            return `
                <tr>
                    <td><code>${m.id.substring(0, 8)}...</code></td>
                    <td><b>${target}</b></td>
                    <td>A cada ${m.check_frequency_minutes} min</td>
                    <td>${statusBadge}</td>
                    <td>${lastCheck}</td>
                    <td>
                        <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 12px;" onclick="checkItemNow('${m.id}')">⚡ Checar</button>
                        <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 12px; color: #ef4444;" onclick="deleteMonitored('${m.id}')">Excluir</button>
                    </td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" style="color: var(--accent-danger); text-align: center;">Erro: ${err.message}</td></tr>`;
    }
}

window.checkItemNow = async function(id) {
    try {
        const res = await fetch(`/api/monitoring/${id}/check-now`, { method: "POST" });
        if (res.ok) {
            alert("Verificação executada com sucesso!");
            loadMonitoringTable();
        } else {
            alert("Falha ao checar item");
        }
    } catch (err) {
        alert("Erro: " + err.message);
    }
};

window.deleteMonitored = async function(id) {
    if (!confirm("Deseja realmente remover este monitoramento?")) return;
    try {
        await fetch(`/api/monitoring/${id}`, { method: "DELETE" });
        loadMonitoringTable();
        loadDashboardMetrics();
    } catch (err) {
        alert("Erro: " + err.message);
    }
};

// ----------------------------------------------------------------------------
// Aba de Conectores
// ----------------------------------------------------------------------------
async function loadConnectorsGrid() {
    const container = document.getElementById("connectors-container");
    container.innerHTML = '<p class="connectors-message">Carregando fontes e conectores...</p>';

    try {
        const res = await fetch("/api/connectors/sites");
        if (!res.ok) {
            let detail = "";
            try {
                const payload = await res.json();
                detail = payload.detail || payload.message || "";
            } catch (err) {
                // A resposta pode não conter JSON.
            }
            throw new Error(detail || `API respondeu HTTP ${res.status} (${res.statusText || "falha na consulta"})`);
        }
        const sites = await res.json();
        if (!Array.isArray(sites)) throw new Error("A API retornou uma lista de fontes inválida.");

        if (sites.length === 0) {
            container.innerHTML = '<div class="connectors-empty"><span>🔌</span><h3>Nenhuma fonte cadastrada</h3><p>Não há sites de busca configurados no banco de dados.</p></div>';
            return;
        }

        container.innerHTML = sites.map(s => `
            <div class="metric-card" style="margin-bottom: 12px;">
                <div class="metric-icon">🔌</div>
                <div style="flex: 1;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="font-size: 16px;">${escapeHtml(s.name)}</h4>
                        <span class="badge ${s.is_active ? "badge-success" : "badge-disabled"}">${s.is_active ? "Fonte ativa" : "Fonte inativa"}</span>
                    </div>
                    <small style="color: var(--text-muted);">${escapeHtml(s.base_url)}</small>
                </div>
                <button class="btn btn-secondary" onclick="testConnector('${s.slug}')">Testar Coleta</button>
            </div>
        `).join("");
    } catch (err) {
        container.innerHTML = `
            <div class="connectors-error" role="alert">
                <div><strong>Não foi possível carregar as fontes.</strong><p>${escapeHtml(err.message || "Falha de comunicação com a API.")}</p></div>
                <button class="btn btn-secondary" type="button" onclick="loadConnectorsGrid()">Tentar novamente</button>
            </div>`;
    }
}

window.loadConnectorsGrid = loadConnectorsGrid;

window.testConnector = async function(slug) {
    try {
        const res = await fetch(`/api/connectors/test/${slug}`, { method: "POST" });
        const data = await res.json();
        if (res.ok) {
            alert(`Conector ${slug} testado com êxito! ${data.items_found} ofertas encontradas.`);
        } else {
            alert(`Falha: ${data.detail}`);
        }
    } catch (err) {
        alert("Erro: " + err.message);
    }
};

// ----------------------------------------------------------------------------
// Configurações & Telegram
// ----------------------------------------------------------------------------
async function loadTelegramStatus() {
    const statusBadge = document.getElementById("telegram-config-status");
    try {
        const res = await fetch("/api/telegram/status");
        const data = await res.json();
        if (data.configured) {
            statusBadge.className = "badge badge-success";
            statusBadge.textContent = "Token Configurado & Ativo";
            if (data.default_chat_id) {
                document.getElementById("input-telegram-chat-id").value = data.default_chat_id;
            }
        } else {
            statusBadge.className = "badge";
            statusBadge.style.background = "#f59e0b";
            statusBadge.textContent = "Token Ausente (configure TELEGRAM_BOT_TOKEN no .env)";
        }
    } catch {
        statusBadge.textContent = "Erro ao consultar status";
    }
}

function initTelegramSettings() {
    document.getElementById("btn-test-telegram").addEventListener("click", async () => {
        const chatId = document.getElementById("input-telegram-chat-id").value.trim();
        try {
            const res = await fetch("/api/telegram/test", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ chat_id: chatId || null })
            });
            const data = await res.json();
            if (data.success) {
                alert("✅ Mensagem de teste enviada com sucesso para o Telegram!");
            } else {
                alert(`❌ Falha no envio: ${data.error || "Verifique o Chat ID e Token"}`);
            }
        } catch (err) {
            alert("Erro na requisição: " + err.message);
        }
    });
}

// ----------------------------------------------------------------------------
// Modals Handling
// ----------------------------------------------------------------------------
function initModals() {
    const modalAdd = document.getElementById("modal-add-url");
    const btnOpenAdd = document.getElementById("btn-open-add-url");
    const btnCloseAdd = document.getElementById("btn-close-modal");
    const btnCancelAdd = document.getElementById("btn-cancel-modal");
    const btnSubmitAdd = document.getElementById("btn-submit-url");
    const errDiv = document.getElementById("modal-url-error");

    btnOpenAdd.addEventListener("click", () => {
        errDiv.style.display = "none";
        document.getElementById("input-custom-url").value = "";
        modalAdd.classList.add("open");
    });

    const closeModal = () => modalAdd.classList.remove("open");
    btnCloseAdd.addEventListener("click", closeModal);
    btnCancelAdd.addEventListener("click", closeModal);

    // Modal Details Close
    document.getElementById("btn-close-details").addEventListener("click", () => {
        document.getElementById("modal-details").classList.remove("open");
    });

    // Submissão do Cadastro por URL
    btnSubmitAdd.addEventListener("click", async () => {
        const url = document.getElementById("input-custom-url").value.trim();
        const targetPrice = document.getElementById("input-target-price").value;
        const freq = document.getElementById("input-frequency").value;

        if (!url) {
            errDiv.textContent = "Por favor, informe a URL do anúncio.";
            errDiv.style.display = "block";
            return;
        }

        errDiv.style.display = "none";
        btnSubmitAdd.disabled = true;
        btnSubmitAdd.textContent = "Extraindo e Validando...";

        try {
            const payload = {
                custom_url: url,
                target_price: targetPrice ? parseFloat(targetPrice) : null,
                check_frequency_minutes: parseInt(freq, 10) || 60
            };

            const res = await fetch("/api/monitoring", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Falha ao cadastrar anúncio.");
            }

            alert("Produto cadastrado com sucesso e adicionado ao monitoramento!");
            closeModal();
            loadDashboardMetrics();
            loadRadarDeals();
        } catch (err) {
            errDiv.textContent = err.message;
            errDiv.style.display = "block";
        } finally {
            btnSubmitAdd.disabled = false;
            btnSubmitAdd.textContent = "Cadastrar & Monitorar";
        }
    });
}

function escapeHtml(text) {
    if (!text) return "";
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

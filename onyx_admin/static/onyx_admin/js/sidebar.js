'use strict';
{
    // Runs inline while the sidebar parses so the recent list is present at first paint.
    const script = document.currentScript;
    const sidebar = script ? script.closest('#nav-sidebar') : null;

    // Hidden columns for this change list are applied before the table exists.
    const bodyClasses = Array.from(document.body.classList);
    const app = bodyClasses.find((name) => name.startsWith('app-'));
    const model = bodyClasses.find((name) => name.startsWith('model-'));
    if (script && bodyClasses.includes('change-list') && app && model) {
        let hidden = [];
        try {
            hidden = JSON.parse(localStorage.getItem('onyx.columns.' + app.slice(4) + '.' + model.slice(6)) || '[]');
        } catch (error) {
            hidden = [];
        }
        if (Array.isArray(hidden) && hidden.length) {
            const style = document.createElement('style');
            style.id = 'onyx-hidden-columns';
            if (script.nonce) {
                style.nonce = script.nonce;
            }
            style.textContent = hidden
                .filter((id) => /^[\w-]+$/.test(id))
                .map((id) => '#result_list .column-' + id + ', #result_list .field-' + id + ' { display: none !important; }')
                .join('\n');
            document.head.append(style);
        }
    }
    let recent = [];
    try {
        recent = JSON.parse(localStorage.getItem('onyx.recent') || '[]');
    } catch (error) {
        recent = [];
    }
    // Collapsed groups are hidden before the app list is parsed.
    if (script && sidebar) {
        let collapsed = [];
        try {
            collapsed = JSON.parse(localStorage.getItem('onyx.sidebar.collapsed') || '[]');
        } catch (error) {
            collapsed = [];
        }
        if (Array.isArray(collapsed) && collapsed.length) {
            const style = document.createElement('style');
            style.id = 'onyx-collapsed-groups';
            if (script.nonce) {
                style.nonce = script.nonce;
            }
            style.textContent = collapsed
                .filter((label) => /^[\w-]+$/.test(label))
                .map((label) => '#nav-sidebar .module.app-' + label + ' tbody { display: none; }')
                .join('\n');
            document.head.append(style);
        }
    }

    if (sidebar && Array.isArray(recent) && recent.length) {
        const module = document.createElement('div');
        module.className = 'module onyx-recent';
        const table = document.createElement('table');
        const caption = document.createElement('caption');
        const title = document.createElement('span');
        title.className = 'section';
        title.textContent = sidebar.dataset.recentLabel || 'Recent';
        caption.append(title);
        table.append(caption);
        const tbody = document.createElement('tbody');
        recent.forEach((item) => {
            if (!item || typeof item.href !== 'string' || typeof item.label !== 'string') {
                return;
            }
            const row = document.createElement('tr');
            if (item.href === location.pathname) {
                row.className = 'current-model';
            }
            const cell = document.createElement('th');
            cell.scope = 'row';
            const link = document.createElement('a');
            link.href = item.href;
            const text = document.createElement('span');
            text.className = 'onyx-recent-label';
            text.textContent = item.label;
            link.append(text);
            cell.append(link);
            row.append(cell);
            tbody.append(row);
        });
        table.append(tbody);
        module.append(table);
        script.insertAdjacentElement('afterend', module);
    }
}

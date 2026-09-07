'use strict';
{
    const isMac = /Mac|iPhone|iPad/.test(navigator.platform);

    function isTyping(target) {
        return target instanceof HTMLElement &&
            (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName));
    }

    // Filter dropdowns navigate to the query string of the chosen option.
    document.addEventListener('change', (event) => {
        const select = event.target;
        if (!(select instanceof HTMLSelectElement) || !select.classList.contains('onyx-filter-select')) {
            return;
        }
        const option = select.options[select.selectedIndex];
        if (option && option.value) {
            window.location.assign(option.value);
        }
    });

    // Text inputs rendered by custom filters outside a form submit on Enter.
    document.addEventListener('keydown', (event) => {
        const input = event.target;
        if (event.key !== 'Enter' || !(input instanceof HTMLInputElement) || input.form || !input.name) {
            return;
        }
        if (!input.closest('#changelist-filter')) {
            return;
        }
        event.preventDefault();
        const url = new URL(window.location.href);
        const value = input.value.trim();
        if (value) {
            url.searchParams.set(input.name, value);
        } else {
            url.searchParams.delete(input.name);
        }
        url.searchParams.delete('p');
        window.location.assign(url.toString());
    });

    // Command palette listing every page reachable from the sidebar.
    function collectItems(sidebar) {
        const items = [];
        const home = sidebar.querySelector('.onyx-nav-home');
        if (home) {
            items.push({label: home.textContent.trim(), group: '', href: home.href, kind: ''});
        }
        sidebar.querySelectorAll('.module').forEach((module) => {
            const caption = module.querySelector('caption .section');
            const group = caption
                ? Array.from(caption.childNodes)
                    .filter((node) => node.nodeType === Node.TEXT_NODE)
                    .map((node) => node.textContent)
                    .join('')
                    .trim()
                : '';
            module.querySelectorAll('tr').forEach((row) => {
                const link = row.querySelector('th a');
                if (!link) {
                    return;
                }
                const label = link.textContent.trim();
                items.push({label, group, href: link.href, kind: ''});
                const add = row.querySelector('td a.addlink');
                if (add) {
                    items.push({label, group, href: add.href, kind: add.textContent.trim()});
                }
            });
        });
        document.querySelectorAll('#user-tools a').forEach((link) => {
            items.push({label: link.textContent.trim(), group: '', href: link.href, kind: 'Go'});
        });
        const logout = document.getElementById('logout-form');
        if (logout) {
            const button = logout.querySelector('button');
            items.push({label: button ? button.textContent.trim() : 'Log out', group: '', kind: 'Action', action: () => logout.requestSubmit()});
        }
        const toggle = document.querySelector('.theme-toggle');
        if (toggle) {
            const label = toggle.querySelector('.visually-hidden');
            const text = label ? label.textContent.replace(/\s*\(.*\)\s*$/, '').trim() : 'Toggle theme';
            items.push({label: text, group: '', kind: 'Action', action: () => toggle.click()});
        }
        return items;
    }

    function score(item, query) {
        if (!query) {
            return 1;
        }
        const haystack = (item.group + ' ' + item.label + ' ' + item.kind).toLowerCase();
        const index = haystack.indexOf(query);
        if (index >= 0) {
            return 1000 - index;
        }
        let matched = 0;
        for (const char of haystack) {
            if (char === query[matched]) {
                matched += 1;
                if (matched === query.length) {
                    return 10;
                }
            }
        }
        return 0;
    }

    function buildPalette(sidebar, trigger) {
        const items = collectItems(sidebar);
        const dialog = document.createElement('dialog');
        dialog.className = 'onyx-palette';
        const input = document.createElement('input');
        input.type = 'search';
        input.autocomplete = 'off';
        input.placeholder = (trigger ? trigger.dataset.placeholder : 'Search') + '…';
        input.setAttribute('aria-label', input.placeholder);
        const list = document.createElement('ul');
        list.setAttribute('role', 'listbox');
        const empty = document.createElement('p');
        empty.className = 'onyx-palette-empty';
        empty.textContent = 'No matches';
        dialog.append(input, list, empty);
        document.body.append(dialog);

        let shown = [];
        let active = 0;

        function go(item) {
            dialog.close();
            if (item.action) {
                item.action();
            } else {
                window.location.assign(item.href);
            }
        }

        function paint() {
            Array.from(list.children).forEach((li, index) => {
                li.setAttribute('aria-selected', index === active ? 'true' : 'false');
            });
            const current = list.children[active];
            if (current) {
                current.scrollIntoView({block: 'nearest'});
            }
        }

        function render() {
            const query = input.value.trim().toLowerCase();
            shown = items
                .map((item, index) => ({item, index, score: score(item, query)}))
                .filter((entry) => entry.score > 0 && (query || !entry.item.kind))
                .sort((a, b) => b.score - a.score || a.index - b.index)
                .slice(0, 10)
                .map((entry) => entry.item);
            list.replaceChildren();
            shown.forEach((item) => {
                const li = document.createElement('li');
                li.setAttribute('role', 'option');
                li.djItem = item;
                if (item.group) {
                    const group = document.createElement('span');
                    group.className = 'onyx-palette-group';
                    group.textContent = item.group;
                    li.append(group);
                }
                const label = document.createElement('span');
                label.className = 'onyx-palette-label';
                label.textContent = item.label;
                li.append(label);
                if (item.kind) {
                    const kind = document.createElement('span');
                    kind.className = 'onyx-palette-kind';
                    kind.textContent = item.kind;
                    li.append(kind);
                }
                list.append(li);
            });
            empty.hidden = shown.length > 0;
            active = 0;
            paint();
        }

        input.addEventListener('input', render);
        input.addEventListener('keydown', (event) => {
            if (event.key === 'ArrowDown') {
                event.preventDefault();
                active = Math.min(active + 1, shown.length - 1);
                paint();
            } else if (event.key === 'ArrowUp') {
                event.preventDefault();
                active = Math.max(active - 1, 0);
                paint();
            } else if (event.key === 'Enter') {
                event.preventDefault();
                if (shown[active]) {
                    go(shown[active]);
                }
            }
        });
        list.addEventListener('mousemove', (event) => {
            const li = event.target.closest('li');
            const index = li ? Array.from(list.children).indexOf(li) : -1;
            if (index >= 0 && index !== active) {
                active = index;
                paint();
            }
        });
        list.addEventListener('click', (event) => {
            const li = event.target.closest('li');
            if (li && li.djItem) {
                go(li.djItem);
            }
        });
        dialog.addEventListener('click', (event) => {
            if (event.target === dialog) {
                dialog.close();
            }
        });

        return {
            open() {
                if (dialog.open) {
                    return;
                }
                input.value = '';
                render();
                dialog.showModal();
                input.focus();
            },
        };
    }

    const RECENT_KEY = 'onyx.recent';

    function readRecent() {
        try {
            const stored = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]');
            return Array.isArray(stored) ? stored : [];
        } catch (error) {
            return [];
        }
    }

    function recordRecent(sidebar) {
        const body = document.body;
        const isList = body.classList.contains('change-list');
        const isChange = body.classList.contains('change-form') && /\/change\/?$/.test(location.pathname);
        if (body.classList.contains('popup') || (!isList && !isChange)) {
            return;
        }
        const current = sidebar.querySelector('.current-model th a');
        const model = current ? current.textContent.trim() : '';
        const subtitle = document.querySelector('.titles > h1 + h2, #content > h1 + h2');
        const heading = document.querySelector('#content h1');
        let label = isList ? model : (subtitle ? subtitle.textContent.trim() : (heading ? heading.textContent.trim() : ''));
        if (!label) {
            return;
        }
        if (label.length > 48) {
            label = label.slice(0, 47) + '…';
        }
        const entry = {href: location.pathname, label};
        const recent = readRecent();
        const index = recent.findIndex((item) => item && item.href === entry.href);
        if (index >= 0) {
            recent[index] = entry;
        } else {
            recent.unshift(entry);
        }
        try {
            localStorage.setItem(RECENT_KEY, JSON.stringify(recent.slice(0, 6)));
        } catch (error) {
            // Storage may be unavailable; the list is a convenience only.
        }
    }

    function columnKey() {
        const classes = Array.from(document.body.classList);
        const app = classes.find((name) => name.startsWith('app-'));
        const model = classes.find((name) => name.startsWith('model-'));
        return app && model ? 'onyx.columns.' + app.slice(4) + '.' + model.slice(6) : null;
    }

    function initColumnChooser(form, measure) {
        const table = document.getElementById('result_list');
        const key = columnKey();
        if (!table || !key) {
            return;
        }
        const columns = Array.from(table.querySelectorAll('thead th'))
            .map((th) => {
                const id = Array.from(th.classList).find((name) => name.startsWith('column-'));
                if (!id || th.classList.contains('action-checkbox-column')) {
                    return null;
                }
                const text = th.querySelector('.text');
                return {id: id.slice(7), label: (text || th).textContent.trim()};
            })
            .filter((column) => column && /^[\w-]+$/.test(column.id));
        if (columns.length < 2) {
            return;
        }

        let hidden = [];
        try {
            hidden = JSON.parse(localStorage.getItem(key) || '[]');
        } catch (error) {
            hidden = [];
        }
        if (!Array.isArray(hidden)) {
            hidden = [];
        }
        hidden = hidden.filter((id) => columns.some((column) => column.id === id));

        let style = document.getElementById('onyx-hidden-columns');
        if (!style) {
            style = document.createElement('style');
            style.id = 'onyx-hidden-columns';
            const own = document.querySelector('script[src*="onyx_admin/js/onyx.js"]');
            if (own && own.nonce) {
                style.nonce = own.nonce;
            }
            document.head.append(style);
        }

        const wrapper = document.createElement('div');
        wrapper.className = 'onyx-columns';
        const toggle = document.createElement('button');
        toggle.type = 'button';
        toggle.className = 'onyx-columns-toggle';
        toggle.setAttribute('aria-haspopup', 'true');
        toggle.setAttribute('aria-expanded', 'false');
        const toggleText = document.createElement('span');
        toggleText.textContent = 'Columns';
        const count = document.createElement('span');
        count.className = 'onyx-columns-count';
        count.hidden = true;
        toggle.append(toggleText, count);
        wrapper.append(toggle);

        const menu = document.createElement('div');
        menu.className = 'onyx-columns-menu';
        menu.hidden = true;
        const title = document.createElement('p');
        title.textContent = 'Show columns';
        menu.append(title);
        const boxes = columns.map((column) => {
            const label = document.createElement('label');
            const box = document.createElement('input');
            box.type = 'checkbox';
            box.value = column.id;
            box.checked = !hidden.includes(column.id);
            label.append(box, document.createTextNode(column.label));
            menu.append(label);
            return box;
        });
        const reset = document.createElement('button');
        reset.type = 'button';
        reset.className = 'onyx-columns-reset';
        reset.textContent = 'Show all';
        menu.append(reset);
        (document.getElementById('container') || document.body).append(menu);

        function apply() {
            style.textContent = hidden
                .map((id) => '#result_list .column-' + id + ', #result_list .field-' + id + ' { display: none !important; }')
                .join('\n');
            count.textContent = String(hidden.length);
            count.hidden = hidden.length === 0;
            const visible = boxes.filter((box) => box.checked);
            boxes.forEach((box) => {
                box.disabled = visible.length === 1 && box.checked;
            });
            try {
                if (hidden.length) {
                    localStorage.setItem(key, JSON.stringify(hidden));
                } else {
                    localStorage.removeItem(key);
                }
            } catch (error) {
                // Storage may be unavailable; the choice still applies to this page.
            }
            if (measure) {
                measure();
            }
        }

        function place() {
            const rect = toggle.getBoundingClientRect();
            const top = Math.min(rect.bottom + 6, window.innerHeight - menu.offsetHeight - 12);
            menu.style.top = Math.round(Math.max(12, top)) + 'px';
            menu.style.right = Math.round(window.innerWidth - rect.right) + 'px';
        }

        function close() {
            if (!menu.hidden) {
                menu.hidden = true;
                toggle.setAttribute('aria-expanded', 'false');
            }
        }

        toggle.addEventListener('click', () => {
            if (menu.hidden) {
                menu.hidden = false;
                place();
                toggle.setAttribute('aria-expanded', 'true');
                const first = menu.querySelector('input:not(:disabled)');
                if (first) {
                    first.focus();
                }
            } else {
                close();
            }
        });
        menu.addEventListener('change', (event) => {
            const box = event.target;
            if (!(box instanceof HTMLInputElement)) {
                return;
            }
            hidden = box.checked ? hidden.filter((id) => id !== box.value) : hidden.concat(box.value);
            apply();
        });
        reset.addEventListener('click', () => {
            hidden = [];
            boxes.forEach((box) => {
                box.checked = true;
            });
            apply();
        });
        document.addEventListener('click', (event) => {
            if (!menu.hidden && !menu.contains(event.target) && !wrapper.contains(event.target)) {
                close();
            }
        });
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && !menu.hidden) {
                close();
                toggle.focus();
            }
        });
        window.addEventListener('scroll', close, {passive: true});
        window.addEventListener('resize', close);

        const bar = form.querySelector('.actions');
        if (bar) {
            bar.append(wrapper);
        } else {
            const tools = document.createElement('div');
            tools.className = 'onyx-table-tools';
            tools.append(wrapper);
            table.closest('.results').before(tools);
        }
        apply();
    }

    function initChangelist() {
        const form = document.getElementById('changelist-form');
        if (!form) {
            return;
        }
        const results = form.querySelector('.results');
        if (results) {
            const fit = () => results.classList.toggle('onyx-fits', results.scrollWidth <= results.clientWidth + 1);
            fit();
            window.addEventListener('resize', fit);
        }
        const actions = form.querySelector('.actions');
        let measure = null;
        if (actions) {
            measure = () => form.style.setProperty('--onyx-actions-h', actions.offsetHeight + 'px');
            const update = () => {
                actions.classList.toggle('onyx-selected', form.querySelector('.action-select:checked') !== null);
                measure();
            };
            form.addEventListener('change', (event) => {
                if (event.target.matches('.action-select, #action-toggle')) {
                    update();
                }
            });
            window.addEventListener('resize', measure);
            update();
        }
        initColumnChooser(form, measure);
        const table = document.getElementById('result_list');
        if (table) {
            const labels = Array.from(table.querySelectorAll('thead th')).map((th) => {
                const text = th.querySelector('.text');
                return th.classList.contains('action-checkbox-column') ? '' : (text || th).textContent.trim();
            });
            table.querySelectorAll('tbody tr').forEach((row) => {
                Array.from(row.children).forEach((cell, index) => {
                    if (cell.tagName === 'TD' && labels[index]) {
                        cell.dataset.label = labels[index];
                    }
                });
            });
        }
        const coarse = window.matchMedia('(pointer: coarse)').matches;
        document.querySelectorAll('#result_list tbody tr').forEach((row) => {
            const link = row.querySelector('th a[href]');
            if (!link || coarse) {
                return;
            }
            row.classList.add('onyx-clickable');
            row.addEventListener('click', (event) => {
                if (event.target.closest('a, input, select, textarea, button, label')) {
                    return;
                }
                if (String(window.getSelection())) {
                    return;
                }
                if (event.metaKey || event.ctrlKey) {
                    window.open(link.href, '_blank');
                } else {
                    window.location.assign(link.href);
                }
            });
        });
    }

    function initChangeForm() {
        const body = document.body;
        if (!body.classList.contains('change-form') || body.classList.contains('popup')) {
            return;
        }
        const form = document.querySelector('#content-main > form');
        if (!form) {
            return;
        }

        const headings = Array.from(form.querySelectorAll('fieldset.module h2.fieldset-heading, .inline-group h2.inline-heading'))
            .filter((heading) => heading.id && heading.textContent.trim());
        if (headings.length >= 3) {
            const toc = document.createElement('nav');
            toc.className = 'onyx-toc';
            toc.setAttribute('aria-label', 'Sections');
            const title = document.createElement('p');
            title.textContent = 'On this page';
            const list = document.createElement('ul');
            const links = headings.map((heading) => {
                const li = document.createElement('li');
                const link = document.createElement('a');
                link.href = '#' + heading.id;
                link.textContent = heading.textContent.trim();
                li.append(link);
                list.append(li);
                return link;
            });
            toc.append(title, list);
            form.append(toc);
            form.classList.add('onyx-has-toc');
            if ('IntersectionObserver' in window) {
                const visible = new Map();
                const observer = new IntersectionObserver((entries) => {
                    entries.forEach((entry) => visible.set(entry.target, entry.isIntersecting));
                    const first = headings.find((heading) => visible.get(heading.closest('fieldset, .inline-group') || heading));
                    links.forEach((link, index) => link.classList.toggle('onyx-active', headings[index] === first));
                }, {rootMargin: '-80px 0px -60% 0px'});
                headings.forEach((heading) => observer.observe(heading.closest('fieldset, .inline-group') || heading));
            }
        }

        let dirty = false;
        let submitting = false;
        const badges = Array.from(form.querySelectorAll('.submit-row')).map((row) => {
            const badge = document.createElement('span');
            badge.className = 'onyx-dirty';
            badge.textContent = 'Unsaved changes';
            badge.hidden = true;
            row.prepend(badge);
            return badge;
        });
        const markDirty = () => {
            if (!dirty) {
                dirty = true;
                badges.forEach((badge) => {
                    badge.hidden = false;
                });
            }
        };
        form.addEventListener('input', markDirty);
        form.addEventListener('change', markDirty);
        form.addEventListener('submit', () => {
            submitting = true;
        });
        window.addEventListener('beforeunload', (event) => {
            if (dirty && !submitting) {
                event.preventDefault();
                event.returnValue = '';
            }
        });
    }

    function initDrawer(sidebar) {
        const button = document.querySelector('.onyx-menu-toggle');
        if (!button) {
            return;
        }
        const phone = window.matchMedia('(max-width: 767px)');
        const backdrop = document.createElement('div');
        backdrop.className = 'onyx-drawer-backdrop';
        document.body.append(backdrop);
        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'onyx-drawer-close';
        closeButton.setAttribute('aria-label', button.getAttribute('aria-label') || 'Close');
        sidebar.prepend(closeButton);
        sidebar.tabIndex = -1;

        const isOpen = () => document.body.classList.contains('onyx-drawer-open');
        const open = () => {
            document.body.classList.add('onyx-drawer-open');
            button.setAttribute('aria-expanded', 'true');
            sidebar.focus({preventScroll: true});
        };
        const close = (refocus) => {
            if (!isOpen()) {
                return;
            }
            document.body.classList.remove('onyx-drawer-open');
            button.setAttribute('aria-expanded', 'false');
            if (refocus) {
                button.focus();
            }
        };

        button.addEventListener('click', () => (isOpen() ? close(true) : open()));
        closeButton.addEventListener('click', () => close(true));
        backdrop.addEventListener('click', () => close(false));
        sidebar.addEventListener('click', (event) => {
            if (phone.matches && event.target.closest('a')) {
                close(false);
            }
        });
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && isOpen()) {
                close(true);
            }
        });
        phone.addEventListener('change', (event) => {
            if (!event.matches) {
                close(false);
            }
        });
    }

    function initGroups(sidebar) {
        const modules = Array.from(sidebar.querySelectorAll('.module[data-app]'));
        if (!modules.length) {
            return;
        }
        const key = 'onyx.sidebar.collapsed';
        let collapsed = [];
        try {
            collapsed = JSON.parse(localStorage.getItem(key) || '[]');
        } catch (error) {
            collapsed = [];
        }
        if (!Array.isArray(collapsed)) {
            collapsed = [];
        }
        let style = document.getElementById('onyx-collapsed-groups');
        if (!style) {
            style = document.createElement('style');
            style.id = 'onyx-collapsed-groups';
            const own = document.querySelector('script[src*="onyx_admin/js/onyx.js"]');
            if (own && own.nonce) {
                style.nonce = own.nonce;
            }
            document.head.append(style);
        }
        const save = () => {
            style.textContent = collapsed
                .filter((label) => /^[\w-]+$/.test(label))
                .map((label) => '#nav-sidebar .module.app-' + label + ' tbody { display: none; }')
                .join('\n');
            try {
                if (collapsed.length) {
                    localStorage.setItem(key, JSON.stringify(collapsed));
                } else {
                    localStorage.removeItem(key);
                }
            } catch (error) {
                // Storage may be unavailable; the state still applies to this page.
            }
        };
        modules.forEach((module) => {
            const label = module.dataset.app;
            const caption = module.querySelector('caption');
            if (!label || !caption) {
                return;
            }
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'onyx-group-toggle';
            const paint = () => {
                const isCollapsed = collapsed.includes(label);
                module.classList.toggle('onyx-collapsed', isCollapsed);
                button.setAttribute('aria-expanded', isCollapsed ? 'false' : 'true');
                button.setAttribute('aria-label', (isCollapsed ? 'Expand ' : 'Collapse ') + label);
            };
            button.addEventListener('click', () => {
                collapsed = collapsed.includes(label) ? collapsed.filter((item) => item !== label) : collapsed.concat(label);
                save();
                paint();
            });
            caption.append(button);
            paint();
        });
    }

    function initLogin() {
        const form = document.getElementById('login-form');
        if (!form) {
            return;
        }
        const password = form.querySelector('input[type="password"]');
        const toggle = form.querySelector('.onyx-password-toggle');
        if (password && toggle) {
            toggle.addEventListener('click', () => {
                const reveal = password.type === 'password';
                password.type = reveal ? 'text' : 'password';
                toggle.setAttribute('aria-pressed', reveal ? 'true' : 'false');
                toggle.setAttribute('aria-label', reveal ? toggle.dataset.hide : toggle.dataset.show);
                password.focus({preventScroll: true});
            });
        }
        const capslock = form.querySelector('.onyx-capslock');
        if (password && capslock) {
            const check = (event) => {
                if (typeof event.getModifierState === 'function') {
                    capslock.hidden = !event.getModifierState('CapsLock');
                }
            };
            password.addEventListener('keydown', check);
            password.addEventListener('keyup', check);
            password.addEventListener('blur', () => {
                capslock.hidden = true;
            });
        }
        let submitted = false;
        form.addEventListener('submit', (event) => {
            if (submitted) {
                event.preventDefault();
                return;
            }
            submitted = true;
            form.classList.add('onyx-submitting');
            const button = form.querySelector('input[type="submit"]');
            if (button) {
                button.setAttribute('aria-busy', 'true');
            }
        });
        window.addEventListener('pageshow', () => {
            submitted = false;
            form.classList.remove('onyx-submitting');
        });
    }

    function init() {
        initLogin();
        const sidebar = document.getElementById('nav-sidebar');
        if (sidebar) {
            initGroups(sidebar);
            initDrawer(sidebar);
            recordRecent(sidebar);
            const toggle = document.getElementById('toggle-nav-sidebar');
            if (toggle) {
                toggle.addEventListener('click', () => sidebar.classList.add('onyx-animate'), {once: true});
            }
        }
        initChangelist();
        initChangeForm();
        const triggers = Array.from(document.querySelectorAll('.onyx-palette-trigger'));
        let palette = null;
        if (sidebar && typeof HTMLDialogElement === 'function') {
            palette = buildPalette(sidebar, triggers[0]);
            triggers.forEach((trigger) => {
                const kbd = trigger.querySelector('kbd');
                if (kbd) {
                    kbd.textContent = isMac ? '⌘K' : 'Ctrl K';
                }
                trigger.addEventListener('click', () => palette.open());
            });
        } else {
            triggers.forEach((trigger) => {
                trigger.hidden = true;
            });
        }

        document.addEventListener('keydown', (event) => {
            if ((event.metaKey || event.ctrlKey) && !event.altKey && event.key.toLowerCase() === 'k') {
                if (palette) {
                    event.preventDefault();
                    palette.open();
                }
                return;
            }
            if (event.key === '/' && !event.metaKey && !event.ctrlKey && !event.altKey && !isTyping(event.target)) {
                const searchbar = document.getElementById('searchbar');
                if (searchbar) {
                    event.preventDefault();
                    searchbar.focus();
                    searchbar.select();
                } else if (palette) {
                    event.preventDefault();
                    palette.open();
                }
            }
        });

        const searchbar = document.getElementById('searchbar');
        if (searchbar && !searchbar.placeholder) {
            searchbar.placeholder = (triggers[0] ? triggers[0].dataset.placeholder : 'Search') + '…';
        }

        // Messages get a dismiss button.
        document.querySelectorAll('ul.messagelist li').forEach((item) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'onyx-dismiss';
            button.setAttribute('aria-label', 'Dismiss');
            button.addEventListener('click', () => item.remove());
            item.append(button);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
}

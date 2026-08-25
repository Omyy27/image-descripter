
    const STORAGE_KEY = 'image_descripter_chats';
    const ACTIVE_KEY = 'image_descripter_active';
    const MAX_CHATS = 10;

    const $ = (id) => document.getElementById(id);
    const formPanel = $('formPanel');
    const chatArea = $('chatArea');
    const chatHistory = $('chat-history');
    const chatInput = $('chat-input');
    const btnSend = $('btn-send');
    const btnNewChat = $('btn-newchat');
    const btnNewChatSide = $('btn-newchat-side');
    const pendingThumbs = $('pending-thumbs');
    const btnAttach = $('btn-attach');
    const attachFile = $('attach-file');
    const sidebar = $('sidebar');
    const chatList = $('chat-list');
    const storageStatus = $('storage-status');
    const chatSearch = $('chat-search');
    const btnToggleSidebar = $('btn-toggle-sidebar');
    const btnCloseSidebar = $('btn-close-sidebar');
    const backdrop = $('backdrop');
    const drop = $('drop');
    const fileInput = $('file');
    const preview = $('preview');
    const dropText = $('drop-text');
    const btn = $('btn');

    let chats = loadChats();
    let currentId = null;
    let pendingImages = [];
    let initialImageB64 = '';

    // ---------- Almacenamiento ----------
    function loadChats() {
      try {
        const raw = sessionStorage.getItem(STORAGE_KEY);
        const arr = raw ? JSON.parse(raw) : [];
        return Array.isArray(arr) ? arr : [];
      } catch { return []; }
    }

    function currentChat() {
      return chats.find(c => c.id === currentId) || null;
    }

    function saveChats() {
      if (chats.length > MAX_CHATS) {
        chats = [...chats].sort((a, b) => b.createdAt - a.createdAt).slice(0, MAX_CHATS);
        if (!currentChat()) currentId = chats[0]?.id || null;
      }
      try {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(chats));
        storageStatus.textContent = '';
      } catch {
        if (chats.length > 1) {
          const oldest = [...chats].sort((a, b) => a.createdAt - b.createdAt)[0];
          chats = chats.filter(c => c.id !== oldest.id);
          if (currentId === oldest.id) currentId = chats[0]?.id || null;
          try {
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify(chats));
            storageStatus.textContent = 'Almacenamiento lleno: se descartó una conversación antigua.';
            renderSidebar();
            renderChat();
            return;
          } catch {}
        }
        storageStatus.textContent = 'Aviso: no se pudo guardar (cuota de sessionStorage llena).';
      }
    }

    function saveActive() {
      try {
        if (currentId) sessionStorage.setItem(ACTIVE_KEY, currentId);
        else sessionStorage.removeItem(ACTIVE_KEY);
      } catch {}
    }

    // ---------- Imágenes ----------
    function compressCanvas(img, maxDim = 1024, quality = 0.8) {
      let { width, height } = img;
      if (width > height && width > maxDim) { height = Math.round(height * maxDim / width); width = maxDim; }
      else if (height >= width && height > maxDim) { width = Math.round(width * maxDim / height); height = maxDim; }
      const canvas = document.createElement('canvas');
      canvas.width = width; canvas.height = height;
      canvas.getContext('2d').drawImage(img, 0, 0, width, height);
      return canvas.toDataURL('image/jpeg', quality).split(',')[1];
    }

    function compressImage(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const img = new Image();
          img.onload = () => resolve(compressCanvas(img));
          img.onerror = reject;
          img.src = reader.result;
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    }

    function setFile(file) {
      if (!file.type.startsWith('image/')) return;
      const reader = new FileReader();
      reader.onload = () => {
        const img = new Image();
        img.onload = () => {
          initialImageB64 = compressCanvas(img);
          preview.src = reader.result;
          preview.classList.remove('hidden');
          dropText.textContent = file.name;
        };
        img.src = reader.result;
      };
      reader.readAsDataURL(file);
    }

    drop.addEventListener('click', () => fileInput.click());
    drop.addEventListener('dragover', (e) => { e.preventDefault(); drop.classList.add('border-app-primary'); });
    drop.addEventListener('dragleave', () => drop.classList.remove('border-app-primary'));
    drop.addEventListener('drop', (e) => {
      e.preventDefault();
      drop.classList.remove('border-app-primary');
      if (e.dataTransfer.files.length) setFile(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener('change', () => {
      if (fileInput.files.length) setFile(fileInput.files[0]);
    });

    btnAttach.addEventListener('click', () => attachFile.click());
    attachFile.addEventListener('change', async () => {
      const files = Array.from(attachFile.files);
      attachFile.value = '';
      for (const f of files) {
        if (!f.type.startsWith('image/')) continue;
        try { pendingImages.push(await compressImage(f)); } catch {}
      }
      renderPendingThumbs();
    });

    function renderPendingThumbs() {
      pendingThumbs.innerHTML = '';
      pendingImages.forEach((b64, i) => {
        const wrap = document.createElement('div');
        wrap.className = 'pending-thumb';
        const img = document.createElement('img');
        img.src = 'data:image/jpeg;base64,' + b64;
        const del = document.createElement('button');
        del.type = 'button';
        del.textContent = '×';
        del.title = 'Quitar imagen';
        del.addEventListener('click', () => { pendingImages.splice(i, 1); renderPendingThumbs(); });
        wrap.appendChild(img);
        wrap.appendChild(del);
        pendingThumbs.appendChild(wrap);
      });
    }

    // ---------- Chat UI ----------
    function escapeHtml(t) {
      const d = document.createElement('div');
      d.textContent = t;
      return d.innerHTML;
    }

    function renderMarkdown(t) {
      if (window.marked && window.DOMPurify) {
        try { return DOMPurify.sanitize(marked.parse(t || '')); } catch {}
      }
      return escapeHtml(t);
    }

    function fmtDur(s) {
      if (s == null || isNaN(s)) return '';
      if (s < 1) return Math.round(s * 1000) + ' ms';
      return s.toFixed(1) + ' s';
    }

    function addBubble(role, text, images, elapsed_s, eval_s) {
      const isUser = role === 'user';
      const wrap = document.createElement('div');
      wrap.className = 'flex flex-col ' + (isUser ? 'items-end ml-auto' : 'items-start') + ' max-w-3xl';

      const meta = document.createElement('div');
      meta.className = 'flex items-center gap-2 mb-2 ' + (isUser ? 'mr-1' : 'ml-1');
      if (!isUser) {
        const ic = document.createElement('div');
        ic.className = 'w-5 h-5 rounded-md bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center';
        ic.innerHTML = '<i class="ph-fill ph-sparkle text-white text-[10px]"></i>';
        meta.appendChild(ic);
      }
      const who = document.createElement('span');
      who.className = 'text-xs text-app-muted';
      who.textContent = isUser ? 'Tú' : 'Image Descripter';
      const tm = document.createElement('span');
      tm.className = 'text-[11px] text-app-muted';
      tm.textContent = new Date().toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
      meta.appendChild(who);
      meta.appendChild(tm);
      if (!isUser && elapsed_s != null) {
        const el = document.createElement('span');
        el.className = 'text-[11px] text-app-muted';
        el.textContent = '· ' + fmtDur(elapsed_s) + (eval_s != null ? ' · eval ' + fmtDur(eval_s) : '');
        meta.appendChild(el);
      }
      wrap.appendChild(meta);

      const body = document.createElement('div');
      body.className = isUser
        ? 'bg-app-primary text-white px-5 py-3.5 rounded-2xl rounded-tr-sm shadow-lg shadow-indigo-500/10 max-w-xl'
        : 'bg-app-panel border border-app-border px-5 py-4 rounded-2xl rounded-tl-sm max-w-xl';

      if (images && images.length) {
        const imgs = document.createElement('div');
        imgs.className = 'flex gap-2 flex-wrap mb-3';
        images.forEach(b64 => {
          const img = document.createElement('img');
          img.src = 'data:image/jpeg;base64,' + b64;
          img.className = 'max-w-[150px] max-h-[150px] rounded-lg object-cover border border-app-border';
          imgs.appendChild(img);
        });
        body.appendChild(imgs);
      }

      const content = document.createElement('div');
      if (isUser) {
        content.className = 'text-sm font-medium whitespace-pre-wrap break-words';
        content.textContent = text;
      } else {
        content.className = 'md';
        content.innerHTML = renderMarkdown(text);
      }
      body.appendChild(content);
      wrap.appendChild(body);
      chatHistory.appendChild(wrap);
      return wrap;
    }

    function renderChat() {
      chatHistory.innerHTML = '';
      const chat = currentChat();
      if (!chat) return;
      chat.messages.forEach(m => addBubble(m.role, m.content, m.images, m.elapsed_s, m.eval_s));
      chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function makeTitle(text) {
      return text.length > 40 ? text.slice(0, 40) + '…' : text;
    }

    function showChat() {
      formPanel.classList.add('hidden');
      chatArea.classList.remove('hidden');
    }

    function showForm() {
      chatArea.classList.add('hidden');
      formPanel.classList.remove('hidden');
    }

    function addTyping() {
      const el = document.createElement('div');
      el.className = 'flex items-center gap-3 pl-1';
      el.innerHTML =
        '<div class="w-6 h-6 rounded-md bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">' +
        '<i class="ph-fill ph-sparkle text-white text-[10px]"></i></div>' +
        '<div class="bg-app-panel border border-app-border rounded-full px-4 py-2.5 flex items-center gap-1.5">' +
        '<span class="w-1.5 h-1.5 rounded-full bg-app-muted typing-dot"></span>' +
        '<span class="w-1.5 h-1.5 rounded-full bg-app-muted typing-dot"></span>' +
        '<span class="w-1.5 h-1.5 rounded-full bg-app-muted typing-dot"></span></div>' +
        '<span class="text-xs text-app-muted">Escribiendo…</span>';
      chatHistory.appendChild(el);
      chatHistory.scrollTop = chatHistory.scrollHeight;
      return el;
    }

    function setBusy(busy) {
      btn.disabled = busy;
      btnSend.disabled = busy;
      btnNewChat.disabled = busy;
      chatInput.disabled = busy;
      btnAttach.disabled = busy;
      btn.classList.toggle('loading', busy);
      btnSend.classList.toggle('loading', busy);
      if (!busy) chatInput.focus();
    }

    async function sendTurn(history, model, chat) {
      const t0 = performance.now();
      const fd = new FormData();
      fd.append('model', model);
      fd.append('messages', JSON.stringify(history));

      setBusy(true);
      showChat();
      const last = history[history.length - 1];
      addBubble('user', last.content, last.images);
      const typing = addTyping();

      try {
        const res = await fetch('/api/chat', { method: 'POST', body: fd });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error del servidor');
        const elapsed_s = (data.timing && data.timing.total_ms != null)
          ? data.timing.total_ms / 1000
          : (performance.now() - t0) / 1000;
        const eval_s = (data.timing && data.timing.eval_ms != null)
          ? data.timing.eval_ms / 1000
          : null;
        chat.messages = [...history, { role: 'assistant', content: data.reply, elapsed_s, eval_s }];
        if (!chat.title || chat.title === 'Nueva conversación') {
          chat.title = makeTitle(last.content);
        }
        saveChats();
        saveActive();
        renderChat();
        renderSidebar();
      } catch (err) {
        typing.remove();
        addBubble('error', 'Error: ' + err.message);
      } finally {
        setBusy(false);
      }
    }

    function startChatFromForm() {
      const context = $('context').value.trim();
      const firstContent = context || 'Describe esta imagen.';
      const model = $('model').value;
      let chat = currentChat();
      if (!chat) {
        chat = { id: genId(), title: 'Nueva conversación', createdAt: Date.now(), model, messages: [] };
        chats.unshift(chat);
        currentId = chat.id;
        saveChats();
        saveActive();
        renderSidebar();
      }
      const userMsg = {
        role: 'user',
        content: firstContent,
        images: initialImageB64 ? [initialImageB64] : undefined
      };
      sendTurn([...chat.messages, userMsg], model, chat);
    }

    btn.addEventListener('click', startChatFromForm);
    $('context').addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); startChatFromForm(); }
    });

    function sendMessage() {
      const chat = currentChat();
      if (!chat) return;
      const text = chatInput.value.trim();
      const images = pendingImages.length ? [...pendingImages] : undefined;
      if (!text && !images) return;
      chatInput.value = '';
      pendingImages = [];
      renderPendingThumbs();
      const content = text || 'Describe esta imagen.';
      const userMsg = { role: 'user', content, images };
      sendTurn([...chat.messages, userMsg], chat.model || $('model-chat').value, chat);
    }

    btnSend.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') sendMessage();
    });

    document.querySelectorAll('.chip').forEach(ch => {
      ch.addEventListener('click', () => {
        chatInput.value = ch.dataset.chip;
        chatInput.focus();
      });
    });

    function genId() {
      return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
    }

    function startNewChat() {
      const cur = currentChat();
      if (cur && cur.messages.length && !confirm('¿Iniciar una nueva conversación? La actual quedará guardada.')) return;
      const chat = { id: genId(), title: 'Nueva conversación', createdAt: Date.now(), model: $('model').value, messages: [] };
      chats.unshift(chat);
      chats = chats.slice(0, MAX_CHATS);
      currentId = chat.id;
      pendingImages = [];
      renderPendingThumbs();
      $('context').value = '';
      chatHistory.innerHTML = '';
      showForm();
      saveChats();
      saveActive();
      renderSidebar();
      closeSidebarMobile();
    }

    btnNewChat.addEventListener('click', startNewChat);
    btnNewChatSide.addEventListener('click', startNewChat);

    // ---------- Sidebar ----------
    function renderSidebar() {
      chatList.innerHTML = '';
      const q = (chatSearch.value || '').trim().toLowerCase();
      const sorted = [...chats]
        .sort((a, b) => b.createdAt - a.createdAt)
        .filter(c => !q || (c.title || '').toLowerCase().includes(q));
      if (!sorted.length) {
        chatList.innerHTML = '<div class="text-xs text-app-muted text-center py-8">' +
          (q ? 'Sin resultados para "' + escapeHtml(q) + '".' : 'Sin conversaciones todavía.') + '</div>';
        return;
      }
      sorted.forEach(c => {
        const item = document.createElement('div');
        item.className = 'flex items-center gap-3 p-2.5 rounded-xl cursor-pointer transition-colors group ' +
          (c.id === currentId ? 'bg-app-panel border-l-2 border-l-app-primary' : 'hover:bg-app-panel/50');
        item.addEventListener('click', () => openChat(c.id));

        const icon = document.createElement('div');
        icon.className = 'w-8 h-8 rounded-lg ' + (c.id === currentId ? 'bg-app-bg' : 'bg-app-panel') + ' flex items-center justify-center shrink-0';
        icon.innerHTML = c.messages.length
          ? '<i class="ph ph-chat-circle-dots ' + (c.id === currentId ? 'text-app-primary' : 'text-app-muted') + '"></i>'
          : '<i class="ph ph-plus text-app-muted"></i>';

        const info = document.createElement('div');
        info.className = 'flex-1 min-w-0';
        const title = document.createElement('p');
        title.className = 'text-sm font-medium truncate';
        title.textContent = c.title || '(sin título)';
        const date = document.createElement('p');
        date.className = 'text-[11px] text-app-muted mt-0.5';
        date.textContent = new Date(c.createdAt).toLocaleString(undefined, { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
        info.appendChild(title);
        info.appendChild(date);

        const del = document.createElement('button');
        del.type = 'button';
        del.className = 'opacity-0 group-hover:opacity-100 text-app-muted hover:text-red-400 transition-all shrink-0';
        del.title = 'Eliminar conversación';
        del.innerHTML = '<i class="ph ph-x"></i>';
        del.addEventListener('click', (e) => { e.stopPropagation(); deleteChat(c.id); });

        item.appendChild(icon);
        item.appendChild(info);
        item.appendChild(del);
        chatList.appendChild(item);
      });
    }

    function openChat(id) {
      const chat = chats.find(c => c.id === id);
      if (!chat) return;
      currentId = id;
      saveActive();
      setModel(chat.model || $('model-chat').value);
      $('context').value = '';
      pendingImages = [];
      renderPendingThumbs();
      syncStatModel();
      if (chat.messages.length) {
        showChat();
        renderChat();
      } else {
        chatHistory.innerHTML = '';
        showForm();
      }
      renderSidebar();
      closeSidebarMobile();
    }

    function deleteChat(id) {
      const chat = chats.find(c => c.id === id);
      if (!chat) return;
      if (chat.messages.length && !confirm('¿Eliminar esta conversación?')) return;
      chats = chats.filter(c => c.id !== id);
      if (currentId === id) {
        currentId = chats[0]?.id || null;
        if (currentId) openChat(currentId);
        else {
          chatHistory.innerHTML = '';
          showForm();
        }
      }
      saveChats();
      saveActive();
      renderSidebar();
    }

    chatSearch.addEventListener('input', renderSidebar);
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        chatSearch.focus();
      }
    });

    btnToggleSidebar.addEventListener('click', () => {
      sidebar.classList.add('mobile-open');
      backdrop.classList.remove('hidden');
    });
    btnCloseSidebar.addEventListener('click', closeSidebarMobile);
    backdrop.addEventListener('click', closeSidebarMobile);
    function closeSidebarMobile() {
      sidebar.classList.remove('mobile-open');
      backdrop.classList.add('hidden');
    }

    // ---------- Estadísticas ----------
    function fmtUptime(s) {
      s = Math.max(0, Math.floor(s));
      const d = Math.floor(s / 86400);
      const h = Math.floor((s % 86400) / 3600);
      const m = Math.floor((s % 3600) / 60);
      if (d) return d + 'd ' + h + 'h ' + m + 'm';
      if (h) return h + 'h ' + m + 'm';
      return m + 'm';
    }

    function syncStatModel() {
      $('stat-model').textContent = $('model-chat').value;
    }

    function setModel(value) {
      $('model').value = value;
      $('model-chat').value = value;
      syncStatModel();
    }

    $('model').addEventListener('change', () => {
      $('model-chat').value = $('model').value;
      syncStatModel();
    });
    $('model-chat').addEventListener('change', () => {
      $('model').value = $('model-chat').value;
      syncStatModel();
      const chat = currentChat();
      if (chat) {
        chat.model = $('model-chat').value;
        saveChats();
      }
    });

    async function refreshStats() {
      try {
        const res = await fetch('/api/stats');
        const d = await res.json();
        $('stat-uptime').textContent = d.uptime != null ? fmtUptime(d.uptime) : '—';
        if (d.cpu != null) {
          $('stat-cpu').textContent = d.cpu + '%';
          $('stat-cpu-bar').style.width = Math.min(100, d.cpu) + '%';
        } else {
          $('stat-cpu').textContent = '—';
        }
        if (d.ram && d.ram.total_mb) {
          $('stat-ram').textContent = (d.ram.used_mb / 1024).toFixed(1) + ' / ' + (d.ram.total_mb / 1024).toFixed(1) + ' GB';
          $('stat-ram-bar').style.width = Math.min(100, d.ram.percent || 0) + '%';
          const ramWarn = $('ram-warning');
          if (d.ram.percent > 90) ramWarn.classList.remove('hidden');
          else ramWarn.classList.add('hidden');
        } else {
          $('stat-ram').textContent = '—';
        }
        const ok = !!d.ollama;
        $('ollama-label').textContent = ok ? 'Modelo activo' : 'Ollama no disponible';
        $('ollama-label').className = ok ? 'text-xs font-medium text-emerald-400' : 'text-xs font-medium text-rose-400';
        $('ollama-dot2').className = ok ? 'relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500' : 'relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500';
        $('ollama-ping').className = ok ? 'animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75' : 'hidden';
        $('ollama-dot').className = ok ? 'w-2.5 h-2.5 rounded-full bg-emerald-500' : 'w-2.5 h-2.5 rounded-full bg-rose-500';
        $('ollama-status').textContent = ok ? 'Conectado en localhost:11434' : 'No conectado';
      } catch {}
    }
    setInterval(refreshStats, 4000);

    // ---------- Restaurar al cargar ----------
    async function populateModels() {
      try {
        const res = await fetch('/api/models');
        const data = await res.json();
        if (data.models && data.models.length) {
          const opts = data.models.map(m => `<option value="${m.value}">${m.label}</option>`).join('');
          $('model').innerHTML = opts;
          $('model-chat').innerHTML = opts;
          return true;
        }
      } catch {}
      return false;
    }

    (async function init() {
      await populateModels();
      const savedActive = sessionStorage.getItem(ACTIVE_KEY);
      if (savedActive && chats.some(c => c.id === savedActive)) currentId = savedActive;
      else if (chats.length) currentId = chats[0].id;
      renderSidebar();
      syncStatModel();
      const chat = currentChat();
      if (chat && chat.messages.length) openChat(chat.id);
      refreshStats();
    })();

    // --- Controles del servidor (dropdown en el header) ---
    const btnServerMenu = $('btn-server-menu');
    const serverMenu = $('server-menu');
    const ctrlStatus = $('ctrl-status');

    function closeServerMenu() {
      serverMenu.classList.add('hidden');
      btnServerMenu.classList.remove('text-white');
    }

    function toggleServerMenu(e) {
      e.stopPropagation();
      const open = serverMenu.classList.toggle('hidden');
      btnServerMenu.classList.toggle('text-white', !open);
    }

    btnServerMenu.addEventListener('click', toggleServerMenu);
    document.addEventListener('click', (e) => {
      if (!serverMenu.classList.contains('hidden') && !serverMenu.contains(e.target)) closeServerMenu();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeServerMenu();
    });

    function ctrlMsg(text, isError) {
      ctrlStatus.textContent = text;
      ctrlStatus.className = 'text-[11px] mt-3 min-h-[1em] ' + (isError ? 'text-rose-400' : 'text-app-muted');
    }

    async function postCtrl(url, body) {
      const res = await fetch(url, { method: 'POST', body });
      return res.json();
    }

    $('btn-reload').addEventListener('click', async () => {
      closeServerMenu();
      const model = $('model-chat').value;
      ctrlMsg('Pre-cargando ' + model + '…');
      try {
        const fd = new FormData();
        fd.append('model', model);
        const data = await postCtrl('/api/reload-model', fd);
        ctrlMsg(data.ok ? data.message : ('Error: ' + (data.error || 'desconocido')), !data.ok);
      } catch (err) {
        ctrlMsg('Error: ' + err.message, true);
      }
    });

    $('btn-unload').addEventListener('click', async () => {
      closeServerMenu();
      const model = $('model-chat').value;
      ctrlMsg('Descargando ' + model + '…');
      try {
        const fd = new FormData();
        fd.append('model', model);
        const data = await postCtrl('/api/unload-model', fd);
        ctrlMsg(data.ok ? data.message : ('Error: ' + (data.error || 'desconocido')), !data.ok);
        refreshStats();
      } catch (err) {
        ctrlMsg('Error: ' + err.message, true);
      }
    });

    $('btn-restart').addEventListener('click', async () => {
      if (!confirm('¿Reiniciar el servidor? La página se recargará en unos segundos.')) return;
      closeServerMenu();
      ctrlMsg('Reiniciando el servidor…');
      try {
        await postCtrl('/api/restart');
        setTimeout(() => { location.reload(); }, 4500);
      } catch (err) {
        ctrlMsg('Error: ' + err.message, true);
      }
    });

    $('btn-stop').addEventListener('click', async () => {
      if (!confirm('¿Detener la app? Ollama seguirá corriendo. Para volver a usarla, relánzala con run.sh / start_windows.bat.')) return;
      closeServerMenu();
      ctrlMsg('Deteniendo la app…');
      try {
        await postCtrl('/api/stop');
        ctrlMsg('App detenida. Relanza con run.sh / start_windows.bat para volver a usarla.');
      } catch (err) {
        ctrlMsg('Error: ' + err.message, true);
      }
    });
  
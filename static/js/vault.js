/* Vault Search & Modal Action Triggers */
document.addEventListener('DOMContentLoaded', () => {
    // Decrypt Modal Trigger
    const decryptBtns = document.querySelectorAll('.btn-trigger-decrypt');
    decryptBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const fileId = btn.getAttribute('data-id');
            const filename = btn.getAttribute('data-name');
            const form = document.getElementById('decrypt-form');
            const nameEl = document.getElementById('decrypt-file-name');

            if (form && nameEl) {
                form.action = `/vault/decrypt/${fileId}`;
                nameEl.textContent = filename;
                openModal('decryptModal');
            }
        });
    });

    // Rename Modal Trigger
    const renameBtns = document.querySelectorAll('.btn-trigger-rename');
    renameBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const fileId = btn.getAttribute('data-id');
            const filename = btn.getAttribute('data-name');
            const form = document.getElementById('rename-form');
            const input = document.getElementById('rename-input');

            if (form && input) {
                form.action = `/vault/rename/${fileId}`;
                input.value = filename;
                openModal('renameModal');
            }
        });
    });

    // Share Modal Trigger
    const shareBtns = document.querySelectorAll('.btn-trigger-share');
    shareBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const fileId  = btn.getAttribute('data-id');
            const filename = btn.getAttribute('data-name');
            const nameEl  = document.getElementById('share-file-name');
            const fileIdEl = document.getElementById('share-file-id');

            if (nameEl) nameEl.textContent = filename;
            if (fileIdEl) fileIdEl.value   = fileId;

            // Always start on step 1
            const s1 = document.getElementById('share-step-1');
            const s2 = document.getElementById('share-step-2');
            if (s1) s1.style.display = 'block';
            if (s2) s2.style.display = 'none';

            openModal('shareModal');
        });
    });
});


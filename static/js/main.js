document.addEventListener('DOMContentLoaded', () => {
    // Flash messages dismissal
    const flashMessages = document.querySelectorAll('.alert');
    if (flashMessages) {
        setTimeout(() => {
            flashMessages.forEach(msg => {
                msg.style.transition = 'opacity 0.5s ease';
                msg.style.opacity = '0';
                setTimeout(() => msg.remove(), 500);
            });
        }, 5000);
    }

    // Page Tabs logic (if any)
    const tabs = document.querySelectorAll('.page-tab');
    const tabContents = document.querySelectorAll('.tab-content');

    if (tabs.length > 0) {
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.getAttribute('data-target');
                
                tabs.forEach(t => t.classList.remove('active'));
                tabContents.forEach(c => c.classList.remove('active'));
                
                tab.classList.add('active');
                document.getElementById(target).classList.add('active');
            });
        });
    }

    // AI Chatbot logic
    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const input = document.getElementById('chat-input');
            const question = input.value;
            if (!question.trim()) return;

            const chatContainer = document.getElementById('chat-container');
            
            // Add user message to UI
            const userMsg = document.createElement('div');
            userMsg.className = 'chat-message chat-user';
            userMsg.textContent = question;
            chatContainer.appendChild(userMsg);
            
            input.value = '';
            chatContainer.scrollTop = chatContainer.scrollHeight;

            // Add loading spinner
            const loadingMsg = document.createElement('div');
            loadingMsg.className = 'chat-message chat-ai';
            loadingMsg.textContent = 'Thinking...';
            chatContainer.appendChild(loadingMsg);

            try {
                const response = await fetch('/ask_ai', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: question })
                });
                
                const data = await response.json();
                
                // Replace loading message
                loadingMsg.innerHTML = data.answer.replace(/\n/g, '<br>');
            } catch (error) {
                loadingMsg.textContent = 'Error communicating with AI.';
            }
            chatContainer.scrollTop = chatContainer.scrollHeight;
        });
    }
});

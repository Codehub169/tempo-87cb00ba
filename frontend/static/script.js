document.addEventListener('DOMContentLoaded', () => {
    const chatWindow = document.getElementById('chatWindow');
    const userMessageInput = document.getElementById('userMessageInput');
    const sendMessageBtn = document.getElementById('sendMessageBtn');
    const systemPromptSelect = document.getElementById('systemPromptSelect');
    const newConversationBtn = document.getElementById('newConversationBtn');
    const geminiApiKeyInput = document.getElementById('geminiApiKey');
    const conversationsList = document.getElementById('conversationsList');

    let currentConversationId = null;

    // Function to format timestamp
    function formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString(); // Adjust as needed for desired format
    }

    // Function to display a message in the chat window
    function displayMessage(sender, content, timestamp = null) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender);

        // Apply markdown formatting for AI messages
        if (sender === 'ai') {
            // Ensure marked.js is loaded before attempting to parse
            if (typeof marked !== 'undefined') {
                messageElement.innerHTML = marked.parse(content);
            } else {
                console.warn('marked.js not loaded. AI message displayed as plain text.');
                messageElement.textContent = content;
            }
        } else {
            messageElement.textContent = content;
        }

        if (timestamp) {
            const timestampElement = document.createElement('span');
            timestampElement.classList.add('timestamp');
            timestampElement.textContent = formatTimestamp(timestamp);
            messageElement.appendChild(timestampElement);
        }

        chatWindow.appendChild(messageElement);
        chatWindow.scrollTop = chatWindow.scrollHeight; // Scroll to bottom
    }

    // Function to fetch and display messages for a conversation
    async function fetchMessages(conversationId) {
        try {
            const response = await fetch(`/api/conversation/${conversationId}/messages`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const messages = await response.json();
            chatWindow.innerHTML = ''; // Clear existing messages
            messages.forEach(msg => {
                displayMessage(msg.sender, msg.content, msg.timestamp);
            });
            currentConversationId = conversationId; // Set current conversation
            // Highlight the active conversation in the sidebar
            document.querySelectorAll('#conversationsList li').forEach(item => {
                item.classList.remove('active');
                if (parseInt(item.dataset.conversationId) === conversationId) {
                    item.classList.add('active');
                }
            });
            displayMessage('ai', `Loaded conversation.`);
        } catch (error) {
            console.error('Error fetching messages:', error);
            displayMessage('ai', 'Error loading messages. Please try starting a new conversation.');
        }
    }

    // Function to load and display conversation history in the sidebar
    async function loadConversations() {
        try {
            const response = await fetch('/api/conversations');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const conversations = await response.json();
            conversationsList.innerHTML = ''; // Clear existing list
            if (conversations.length === 0) {
                const noConvoItem = document.createElement('li');
                noConvoItem.textContent = 'No past conversations.';
                conversationsList.appendChild(noConvoItem);
                return;
            }

            conversations.forEach(convo => {
                const listItem = document.createElement('li');
                listItem.dataset.conversationId = convo.id; // Store ID for easy access
                const promptSnippet = convo.system_prompt_used.substring(0, 30) + '...';
                const date = new Date(convo.created_at).toLocaleDateString();
                // Add delete button
                listItem.innerHTML = `<span>${promptSnippet}</span><span style="font-size:0.8em; color:#888;">${date}</span><button class="delete-conversation-btn" data-id="${convo.id}">🗑️</button>`;
                
                listItem.addEventListener('click', (event) => {
                    // Only fetch messages if the click wasn't on the delete button
                    if (!event.target.classList.contains('delete-conversation-btn')) {
                        fetchMessages(convo.id);
                    }
                });

                // Add event listener for the delete button
                const deleteBtn = listItem.querySelector('.delete-conversation-btn');
                deleteBtn.addEventListener('click', (event) => {
                    event.stopPropagation(); // Prevent the parent <li>'s click event
                    deleteConversation(convo.id);
                });

                conversationsList.appendChild(listItem);
            });

            // If there's an active conversation, highlight it
            if (currentConversationId) {
                document.querySelectorAll('#conversationsList li').forEach(item => {
                    if (parseInt(item.dataset.conversationId) === currentConversationId) {
                        item.classList.add('active');
                    }
                });
            }

        } catch (error) {
            console.error('Error loading conversations:', error);
            const errorItem = document.createElement('li');
            errorItem.textContent = 'Error loading conversations.';
            conversationsList.appendChild(errorItem);
        }
    }

    // Function to start a new conversation
    async function startNewConversation() {
        const selectedPrompt = systemPromptSelect.value;
        const apiKey = geminiApiKeyInput.value.trim();

        if (!apiKey) {
            displayMessage('ai', 'Please enter your Gemini API Key before starting a new conversation.');
            return;
        }

        try {
            const response = await fetch('/api/conversation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ system_prompt_used: selectedPrompt }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const conversation = await response.json();
            currentConversationId = conversation.id;
            chatWindow.innerHTML = ''; // Clear chat window for new conversation
            displayMessage('ai', `New conversation started with prompt: "${selectedPrompt}"`);
            console.log('New conversation started:', conversation);
            await loadConversations(); // Reload conversations to show the new one
            // Highlight the new conversation
            document.querySelectorAll('#conversationsList li').forEach(item => {
                item.classList.remove('active');
                if (parseInt(item.dataset.conversationId) === currentConversationId) {
                    item.classList.add('active');
                }
            });

        } catch (error) {
            console.error('Error starting new conversation:', error);
            displayMessage('ai', 'Error starting new conversation. Please try again.');
        }
    }

    // Function to send a user message and get AI response
    async function sendMessage() {
        const messageContent = userMessageInput.value.trim();
        const apiKey = geminiApiKeyInput.value.trim();

        if (!messageContent) return;
        if (currentConversationId === null) {
            displayMessage('ai', 'Please start a new conversation first.');
            return;
        }
        if (!apiKey) {
            displayMessage('ai', 'Please enter your Gemini API Key before sending a message.');
            return;
        }

        displayMessage('user', messageContent, new Date().toISOString()); // Display user message immediately
        userMessageInput.value = ''; // Clear input field

        try {
            const response = await fetch(`/api/conversation/${currentConversationId}/send_message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message_content: messageContent, api_key: apiKey }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const aiMessage = await response.json();
            displayMessage('ai', aiMessage.content, aiMessage.timestamp);
        } catch (error) {
            console.error('Error sending message or getting AI response:', error);
            displayMessage('ai', 'Error getting AI response. Please try again.');
        }
    }

    // New function to delete a conversation
    async function deleteConversation(conversationId) {
        if (!confirm('Are you sure you want to delete this conversation? This action cannot be undone.')) {
            return;
        }
        try {
            const response = await fetch(`/api/conversation/${conversationId}`, {
                method: 'DELETE',
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            displayMessage('ai', `Conversation ${conversationId} deleted.`);
            if (currentConversationId === conversationId) {
                currentConversationId = null;
                chatWindow.innerHTML = ''; // Clear chat window
                displayMessage('ai', 'Conversation deleted. Please start a new conversation.');
            }
            await loadConversations(); // Reload conversations list
        } catch (error) {
            console.error('Error deleting conversation:', error);
            displayMessage('ai', 'Error deleting conversation. Please try again.');
        }
    }

    // Event Listeners
    newConversationBtn.addEventListener('click', startNewConversation);
    sendMessageBtn.addEventListener('click', sendMessage);
    userMessageInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });

    // Initial setup: Load past conversations and prompt the user
    loadConversations();
    displayMessage('ai', 'Welcome to PromptCraft AI Chat! Please enter your Gemini API Key, then choose a system prompt and click "Start New Conversation" to begin.');
});

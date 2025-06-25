document.addEventListener('DOMContentLoaded', () => {
    const chatWindow = document.getElementById('chatWindow');
    const userMessageInput = document.getElementById('userMessageInput');
    const sendMessageBtn = document.getElementById('sendMessageBtn');
    const systemPromptSelect = document.getElementById('systemPrompt');
    const newConversationBtn = document.getElementById('newConversationBtn');
    const geminiApiKeyInput = document.getElementById('geminiApiKey'); // New: Get API Key input

    let currentConversationId = null;

    // Function to display a message in the chat window
    function displayMessage(sender, content) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender);
        messageElement.textContent = content;
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
                displayMessage(msg.sender, msg.content);
            });
        } catch (error) {
            console.error('Error fetching messages:', error);
            displayMessage('ai', 'Error loading messages. Please try starting a new conversation.');
        }
    }

    // Function to start a new conversation
    async function startNewConversation() {
        const selectedPrompt = systemPromptSelect.value;
        const apiKey = geminiApiKeyInput.value.trim(); // Get API key

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
        } catch (error) {
            console.error('Error starting new conversation:', error);
            displayMessage('ai', 'Error starting new conversation. Please try again.');
        }
    }

    // Function to send a user message and get AI response
    async function sendMessage() {
        const messageContent = userMessageInput.value.trim();
        const apiKey = geminiApiKeyInput.value.trim(); // Get API key

        if (!messageContent) return;
        if (currentConversationId === null) {
            displayMessage('ai', 'Please start a new conversation first.');
            return;
        }
        if (!apiKey) {
            displayMessage('ai', 'Please enter your Gemini API Key before sending a message.');
            return;
        }

        displayMessage('user', messageContent);
        userMessageInput.value = ''; // Clear input field

        try {
            const response = await fetch(`/api/conversation/${currentConversationId}/send_message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message_content: messageContent, api_key: apiKey }), // Include API key
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const aiMessage = await response.json();
            displayMessage('ai', aiMessage.content);
        } catch (error) {
            console.error('Error sending message or getting AI response:', error);
            displayMessage('ai', 'Error getting AI response. Please try again.');
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

    // Initial setup: Try to start a default conversation or prompt the user
    // For simplicity, we'll just prompt the user to start a new conversation initially.
    displayMessage('ai', 'Welcome to PromptCraft AI Chat! Please enter your Gemini API Key, then select a system prompt and click "Start New Conversation" to begin.');
});